/**
 * This module provides the user space direct access to physical memory.
 * In this it mimics the behaviour of /dev/mem.
 *
 * See phys_mem.h for a complete documentation!
 *
 *
 * Acknowledgements:
 * =======================
 *
 * This code has been written by taking  example code from the
 * LDD-book [1] as a cure for the "I do not like empty source-files"-symptom.
 * Alessandro & Jonathan: Thank you!
 *
 * [1]  "Linux Device Drivers" by Alessandro Rubini and Jonathan Corbet,
 *       published by O'Reilly & Associates."
 */
/*
    Copyright (C) 2010  Jens Neuhalfen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#define DRIVER_AUTHOR "Jens Neuhalfen <jens@neuhalfen.name>"
#define DRIVER_DESC   "Accessing raw memory from userspace, but in a controlled manner."

#define CHAR_DEVICE_NAME "phys_mem"
#define DEVICE_CLASS_NAME "phys_mem"
#define DEVICE_FILE_NAME "phys_mem"

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/init.h>
#include <linux/kernel.h>	/* printk() */
#include <linux/slab.h>		/* kmalloc() */
#include <linux/fs.h>		/* everything... */
#include <linux/errno.h>	/* error codes */
#include <linux/types.h>	/* size_t */
#include <linux/proc_fs.h>
#include <linux/fcntl.h>	/* O_ACCMODE */
#include <linux/aio.h>
#include <asm/uaccess.h>
#include <linux/mm.h>
#include <linux/device.h>

#include "phys_mem_int.h"           /* local definitions */


int phys_mem_major = PHYS_MEM_MAJOR;
int phys_mem_devs = 1; /* number of bare phys_mem devices */

static struct class *device_class;

struct phys_mem_dev *phys_mem_devices; /* allocated in phys_mem_init */

void phys_mem_cleanup(void);




/* declare one cache pointer: use it for all session */
struct kmem_cache *session_mem_cache;

/*
 * Free all frame-stati in session->frame_stati  and
 * reset the session so, that the frame-stati-part is
 * 'Unconfigured'
 * Claimed pages in the frame-stati are freed.
 *
 *  The session lock must be held, when calling this function.
 */
void free_page_stati(struct phys_mem_session* session) {


    if (session->frame_stati) {
        if (session->num_frame_stati) {
            size_t i;

            for (i = 0; i < session->num_frame_stati; i++) {
                struct page* p = session->frame_stati[i].page;
                if (p) {
                    session->frame_stati[i].page = NULL;

                    if (page_count(p)) {
                        printk(KERN_DEBUG "Session %llu: Freeing page #%lu @%lu with page_count %u\n", session->session_id, page_to_pfn(p), i, page_count(p));
                        __free_pages(p, 0);
                    } else {
                        printk(KERN_WARNING "Session %llu: NOT freeing page #%lu @%lu with page_count %u\n", session->session_id, page_to_pfn(p), i, page_count(p));
                    }
                }
            }
        }
        SESSION_FREE_FRAME_STATI(session->frame_stati);
    }
    session->num_frame_stati = 0;
    session->frame_stati = NULL;
}

static void phys_mem_setup_cdev(struct phys_mem_dev *dev, int index) {
    int err, devno = MKDEV(phys_mem_major, index);

    cdev_init(&dev->cdev, &phys_mem_fops);
    dev->cdev.owner = THIS_MODULE;
    dev->cdev.ops = &phys_mem_fops;
    err = cdev_add(&dev->cdev, devno, 1);
    /* Fail gracefully if need be */
    if (err)
        printk(KERN_NOTICE "Error %d adding "CHAR_DEVICE_NAME"%d", err, index);
}




/*
 * Finally, the module stuff
 */
#define PRINT_SIZE(t)  printk(KERN_NOTICE "sizeof(%s)\t= %lu\n", #t ,sizeof(t))

int phys_mem_init(void) {
    int result, i;
    dev_t dev = MKDEV(phys_mem_major, 0);

    /*
     * Register your major, and accept a dynamic number.
     */
    if (phys_mem_major)
        result = register_chrdev_region(dev, phys_mem_devs, CHAR_DEVICE_NAME);
    else {
        result = alloc_chrdev_region(&dev, 0, phys_mem_devs, CHAR_DEVICE_NAME);
        phys_mem_major = MAJOR(dev);
    }
    if (result < 0)
        return result;

    device_class = class_create(THIS_MODULE, DEVICE_CLASS_NAME);
    if (IS_ERR(device_class)) {
        printk(KERN_WARNING "no udev support\n");
    }

    phys_mem_devices = kmalloc(phys_mem_devs * sizeof (struct phys_mem_dev), GFP_KERNEL);
    if (!phys_mem_devices) {
        result = -ENOMEM;
        goto fail_malloc;
    }
    memset(phys_mem_devices, 0, phys_mem_devs * sizeof (struct phys_mem_dev));
    for (i = 0; i < phys_mem_devs; i++) {
        sema_init(&phys_mem_devices[i].sem, 1);
        phys_mem_setup_cdev(phys_mem_devices + i, i);
        if (!IS_ERR(device_class)) {
            device_create(device_class, NULL, MKDEV(phys_mem_major, i), NULL, CHAR_DEVICE_NAME);
        }

    }

    session_mem_cache = kmem_cache_create("session_mem", sizeof (struct phys_mem_session),
            0, SLAB_HWCACHE_ALIGN, NULL); /* no ctor/dtor */
    if (!session_mem_cache) {
        phys_mem_cleanup();
        return -ENOMEM;
    }



    PRINT_SIZE(void*);
    PRINT_SIZE(short);
    PRINT_SIZE(int);
    PRINT_SIZE(long);
    PRINT_SIZE(long long);

    printk(KERN_NOTICE "IOCTL for PHYS_MEM_IOC_MARK_FRAME_BAD: 0x%lx\n", PHYS_MEM_IOC_MARK_FRAME_BAD);
    PRINT_SIZE(struct mark_page_poison);

    printk(KERN_NOTICE "IOCTL for PHYS_MEM_IOC_REQUEST_PAGES: 0x%lx\n", PHYS_MEM_IOC_REQUEST_PAGES);
    PRINT_SIZE(struct phys_mem_request);
    PRINT_SIZE(struct phys_mem_frame_status);
    PRINT_SIZE(struct phys_mem_frame_request);

    return 0; /* succeed */

fail_malloc:
    unregister_chrdev_region(dev, phys_mem_devs);
    return result;
}

void phys_mem_cleanup(void) {
    int i;

    if (!IS_ERR(device_class)) {
        for (i = 0; i < phys_mem_devs; i++) {
            device_destroy(device_class, MKDEV(phys_mem_major, i));
        }
        class_destroy(device_class);
    }

    for (i = 0; i < phys_mem_devs; i++) {
        cdev_del(&phys_mem_devices[i].cdev);
    }
    kfree(phys_mem_devices);

    if (session_mem_cache)
        kmem_cache_destroy(session_mem_cache);
    unregister_chrdev_region(MKDEV(phys_mem_major, 0), phys_mem_devs);
}

MODULE_LICENSE("GPL");
MODULE_AUTHOR(DRIVER_AUTHOR);
MODULE_DESCRIPTION(DRIVER_DESC);

module_init(phys_mem_init);
module_exit(phys_mem_cleanup);
