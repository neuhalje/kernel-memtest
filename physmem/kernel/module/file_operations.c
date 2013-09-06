/**
 * This module provides the user space direct access to physical memory.
 * In this it mimics the behaviour of /dev/mem.
 *
 * See phys_mem.h for a complete documentation!
 *
 * Certain operations are only valid in certain states of the session.
 *
 * This implementation uses state-based dispatching to call the right
 * action for the current session state.
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
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/init.h>
#include <linux/kernel.h>       /* printk() */
#include <linux/fs.h>           /* everything... */
#include <linux/errno.h>        /* error codes */
#include <linux/types.h>        /* size_t */
#include <linux/fcntl.h>        /* O_ACCMODE */
#include <asm/uaccess.h>

#include <linux/slab.h>

#include "phys_mem.h"           /* local definitions */
#include "phys_mem_int.h"           /* local definitions */
#include "page_claiming.h"           /* local definitions */
#include "mmap_phys.h"

/*
 * Open and close
 */

atomic64_t session_counter = ATOMIC_INIT(0);

int phys_mem_open(struct inode *inode, struct file *filp) {
    struct phys_mem_dev *dev; /* device information */
    struct phys_mem_session* session; /* the to-be created session */

    /*  Find the device */
    dev = container_of(inode->i_cdev, struct phys_mem_dev, cdev);

    session = kmem_cache_alloc(session_mem_cache, GFP_KERNEL);

    if (!session)
        return -ENOMEM;

    session->session_id = atomic64_add_return(1, &session_counter);
    session->device = dev;
    sema_init(&session->sem, 1);
    session->vmas = 0;
    session->num_frame_stati = 0;
    session->frame_stati = NULL;
    session->status.state = SESSION_STATE_INVALID;

    SET_STATE(session, SESSION_STATE_OPEN);


    /* and use filp->private_data to point to the device data */
    filp->private_data = session;

    return 0; /* success */
}

int phys_mem_release(struct inode *inode, struct file *filp) {
    struct phys_mem_session* session; /* the to-be destroyed session */

    session = (struct phys_mem_session*) filp->private_data;

    if (down_interruptible(&session->sem))
        return -ERESTARTSYS;


    // Depending on the state of the session we need to do several
    // steps. This "fast'n'furious" implementation of the state
    // machine is chosen over the 'real' steps because
    // this way it is much cleaner.

    while (GET_STATE(session) != SESSION_STATE_CLOSED) {
        switch (GET_STATE(session)) {

            case SESSION_STATE_OPEN:
                //  Release all resources aquired in open (except the session and the lock)
                session->device = NULL;
                session->vmas = 0;

                SET_STATE(session, SESSION_STATE_CLOSED);
                break;

            case SESSION_STATE_CONFIGURING:
                // Bad: We need to wait until
                //      we have a valid state again
                //      In theory this could go on for ever.
                printk(KERN_WARNING "Session %llu: Releasing device while it is impossible (SESSION_STATE_CONFIGURING)\n", session->session_id);
                up(&session->sem);
                return -ERESTARTSYS;
                break;

            case SESSION_STATE_CONFIGURED:
                // Free all claimed pages

                free_page_stati(session);
                SET_STATE(session, SESSION_STATE_OPEN);
                break;

            case SESSION_STATE_MAPPED: break;
                // Hope that all mappings have been taken care of ...
                if (session->vmas)
                    printk(KERN_NOTICE "Session %llu: Releasing device while it still holds %d mappings (SESSION_STATE_MAPPED)\n ", session->session_id, session->vmas);

                SET_STATE(session, SESSION_STATE_CONFIGURED);
                break;
        }
    }

    up(&session->sem);
    kmem_cache_free(session_mem_cache, session);
    return 0;
}

/*
 * Data management: read and write
 */

/**
 * Read: Read session->frame_stati
 *
 * This assumes that the session is in SESSION_STATE_CONFIGURED or SESSION_STATE_MAPPED
 */
ssize_t file_read_configured(struct file *filp, char __user *buf, size_t count,
        loff_t *f_pos) {
    ssize_t retval = 0, max_size = 0;

    struct phys_mem_session* session = (struct phys_mem_session*) filp->private_data;

    if (down_interruptible(&session->sem))
        return -ERESTARTSYS;

    if ((GET_STATE(session) != SESSION_STATE_CONFIGURED)
            && (GET_STATE(session) != SESSION_STATE_MAPPED)) {
        retval = -EIO;
        printk(KERN_NOTICE "Session %llu: The session cannot be read in state %i", session->session_id, GET_STATE(session));
        goto nothing;
    }

    max_size = SESSION_FRAME_STATI_SIZE(session->num_frame_stati);


    if (*f_pos > max_size)
        goto nothing;
    if (*f_pos + count > max_size)
        count = max_size - *f_pos;

    if (copy_to_user(buf, ((void*) ((unsigned long) session->frame_stati) + *f_pos), count)) {
        retval = -EFAULT;
        goto nothing;
    }

    printk(KERN_DEBUG "Session %llu:  read OK   %08lli, %zi with max_size: %zi  From %lli to %lli \n", session->session_id, *f_pos, count, max_size, *f_pos, *f_pos + count);

    up(&session->sem);


    *f_pos += count;
    return count;

nothing:
    printk(KERN_DEBUG "Session %llu:  read ERR  %08lli, %zi with max_size: %zi (p+s = %lli) -> %zi\n", session->session_id, *f_pos, count, max_size, *f_pos + count, retval);
    up(&session->sem);
    return retval;
}

/*
 * The ioctl() implementation
 * We are NOT locking the session because the specific implementations will
 * take care of that!
 */
int file_ioctl_open(struct inode *inode, struct file *filp,
        unsigned int cmd, unsigned long arg) {

    int err = 0, ret = 0;
    struct phys_mem_session* session = (struct phys_mem_session*) filp->private_data;

    printk(KERN_DEBUG "Session %llu: file_ioctl_open: %x Type: %c (expect %c), Number %i Arg: %p\n", session->session_id, cmd, _IOC_TYPE(cmd), PHYS_MEM_IOC_MAGIC, _IOC_NR(cmd), (void*) arg);

    /* don't even decode wrong cmds: better returning  ENOTTY than EFAULT */
    if (_IOC_TYPE(cmd) != PHYS_MEM_IOC_MAGIC) return -ENOTTY;
    if (_IOC_NR(cmd) > PHYS_MEM_IOC_MAXNR) return -ENOTTY;

    /*
     * the type is a bitmask, and VERIFY_WRITE catches R/W
     * transfers. Note that the type is user-oriented, while
     * verify_area is kernel-oriented, so the concept of "read" and
     * "write" is reversed
     */
    if (_IOC_DIR(cmd) & _IOC_READ) {
        err = !access_ok(VERIFY_WRITE, (void __user *) arg, _IOC_SIZE(cmd));
    } else if (_IOC_DIR(cmd) & _IOC_WRITE) {
        err = !access_ok(VERIFY_READ, (void __user *) arg, _IOC_SIZE(cmd));
    }
    if (err)
        return -EFAULT;

    switch (cmd) {
        case PHYS_MEM_IOC_REQUEST_PAGES:
        {
            /*  arg points to the struct phys_mem_request */
            struct phys_mem_request request;

            if (copy_from_user(&request, (struct phys_mem_request __user *) arg, sizeof (struct phys_mem_request))) {
                printk(KERN_DEBUG "Session %llu: file_ioctl_open: copy_from_user failed. \n", session->session_id);
                ret = -EFAULT;
            } else {
                printk(KERN_DEBUG "Session %llu: request: Ver %lu, %lu items @%p\n", session->session_id, request.protocol_version, request.num_requests, request.req);
                if (request.protocol_version != IOCTL_REQUEST_VERSION)
                    ret = -EINVAL;
                else
                    ret = handle_request_pages(session, &request);
            }
            break;
        }
        case PHYS_MEM_IOC_MARK_FRAME_BAD:
        {
            /*  arg points to the struct mark_page_poison */
            struct mark_page_poison request;

            if (copy_from_user(&request, (struct mark_page_poison __user *) arg, sizeof (struct mark_page_poison))) {
                printk(KERN_DEBUG "Session %llu: file_ioctl_open: copy_from_user failed. \n", session->session_id);
                ret = -EFAULT;
            } else {
                printk(KERN_DEBUG "Session %llu: request: Ver %lu,  pfn: %lu  \n", session->session_id, request.protocol_version, request.bad_pfn);
                if (request.protocol_version != IOCTL_REQUEST_VERSION)
                    ret = -EINVAL;
                else
                    ret = handle_mark_page_poison(session, &request);
            }
            break;
        }


        default: /* redundant, as cmd was checked against MAXNR */
            printk(KERN_DEBUG "Session %llu: file_ioctl_open: default %d\n", session->session_id, cmd);
            return -ENOTTY;
    }

    return ret;
}

/**
 * seek the read-buffer
 */
loff_t file_llseek_configured(struct file *filp, loff_t off, int whence) {

    struct phys_mem_session* session = (struct phys_mem_session*) filp->private_data;

    size_t max_size = 0;

    long newpos = 0;
    long error = 0;

    if (down_interruptible(&session->sem))
        return -ERESTARTSYS;

    if ((GET_STATE(session) != SESSION_STATE_CONFIGURED)
            && (GET_STATE(session) != SESSION_STATE_MAPPED)) {
        error = -EIO;
        printk(KERN_NOTICE "Session %llu: The session cannot be llseek in state %i", session->session_id, GET_STATE(session));
        goto err;
    }

    max_size = SESSION_FRAME_STATI_SIZE(session->num_frame_stati);

    switch (whence) {
        case 0: /* SEEK_SET */
            newpos = off;
            break;

        case 1: /* SEEK_CUR */
            newpos = filp->f_pos + off;
            break;

        case 2: /* SEEK_END */
            newpos = max_size + off;
            break;

        default: /* can't happen */
            error = -EINVAL;
            goto err;
    }
    if (newpos < 0) {
        error = -EINVAL;
        goto err;
    }
    printk(KERN_DEBUG "Session %llu:  llseek OK   %08lli, %i with max_size: %li  From %lli to %li \n", session->session_id, off, whence, max_size, filp->f_pos, newpos);
    filp->f_pos = newpos;


    up(&session->sem);
    return newpos;
err:
    printk(KERN_DEBUG "Session %llu:  llseek ERR  %08lli, %i with max_size: %li  From %lli to %li \n", session->session_id, off, whence, max_size, filp->f_pos, newpos);
    up(&session->sem);
    return error;
}





/*
 * The fops
 */


/**
 * The file operations indexed by the session state. Dispatcher functions
 * extract the sessionstate from the file* and call the matching implementation
 * fops_by_session_state[status].op
 *
 */
struct file_operations fops_by_session_state[] = {
    {
        /* CLOSED */
        .llseek = NULL,
        .read = NULL,
        .ioctl = NULL,
        .mmap = NULL,
    },
    {
        /* OPEN */
        .llseek = NULL,
        .read = NULL,
        .ioctl = file_ioctl_open,
        .mmap = NULL,
    },
    {
        /* CONFIGURING */
        .llseek = NULL,
        .read = NULL,
        .ioctl = NULL,
        .mmap = NULL,
    },
    {
        /* CONFIGURED */
        .llseek = file_llseek_configured,
        .read = file_read_configured,
        .ioctl = file_ioctl_open,
        .mmap = file_mmap_configured,
    },
    {
        /* MAPPED */
        .llseek = file_llseek_configured,
        .read = file_read_configured,
        .ioctl = NULL,
        .mmap = file_mmap_configured,
    },
};

loff_t dispatch_llseek(struct file *filp, loff_t off, int whence) {
    struct phys_mem_session * session = filp->private_data;
    loff_t(*fn) (struct file *, loff_t, int);

    if (session->status.state >= SESSION_NUM_STATES) {
        printk(KERN_ERR "Seeking with an invalid session state of %i!\n", session->status.state);
        return -EIO;
    };


    fn = fops_by_session_state[session->status.state].llseek;

    if (fn)
        return fn(filp, off, whence);
    else {
        printk(KERN_NOTICE "Session %llu:  llseek not supported in state %i\n", session->session_id, session->status.state);
        return -EIO;
    }
}

ssize_t dispatch_read(struct file *filp, char __user *buf, size_t count,
        loff_t *f_pos) {

    struct phys_mem_session * session = filp->private_data;
    ssize_t(*fn) (struct file *, char __user *, size_t, loff_t *);

    if (session->status.state >= SESSION_NUM_STATES) {
        printk(KERN_ERR "Reading with an invalid session state of %i!\n", session->status.state);
        return -EIO;
    };

    fn = fops_by_session_state[session->status.state].read;

    if (fn)
        return fn(filp, buf, count, f_pos);
    else {
        printk(KERN_NOTICE "Session %llu:  read not supported in state %i\n", session->session_id, session->status.state);
        return -EIO;
    }
}

int dispatch_ioctl(struct inode *inode, struct file *filp,
        unsigned int cmd, unsigned long arg) {

    struct phys_mem_session * session = filp->private_data;
    int (*fn) (struct inode *, struct file *, unsigned int, unsigned long);
    printk(KERN_ERR "IOCTL:session state of %i!\n", session->status.state);

    if (session->status.state >= SESSION_NUM_STATES) {
        printk(KERN_ERR "IOCTL with an invalid session state of %i!\n", session->status.state);
        return -EIO;
    };

    fn = fops_by_session_state[session->status.state].ioctl;

    if (fn)
        return fn(inode, filp, cmd, arg);
    else {
        printk(KERN_NOTICE "Session %llu:  ioctl not supported in state %i\n", session->session_id, session->status.state);
        return -EIO;
    }
}

int dispatch_mmap(struct file * filp, struct vm_area_struct * vma) {

    struct phys_mem_session * session = filp->private_data;
    int (*fn) (struct file *, struct vm_area_struct *);
    printk(KERN_NOTICE "Session %llu:  mmap \n", (session->session_id));

    if (session->status.state >= SESSION_NUM_STATES) {
        printk(KERN_ERR "mmap with an invalid session state of %i!\n", session->status.state);
        return -EIO;
    };

    fn = fops_by_session_state[session->status.state].mmap;

    if (fn)
        return fn(filp, vma);
    else {
        printk(KERN_NOTICE "Session %llu:  mmap not supported in state %i \n", session->session_id, session->status.state);
        return -EIO;
    }
}


struct file_operations phys_mem_fops = {
    .owner = THIS_MODULE,
    .llseek = dispatch_llseek,
    .read = dispatch_read,
    .ioctl = dispatch_ioctl,
    .open = phys_mem_open,
    .release = phys_mem_release,
    .mmap = dispatch_mmap,
};
