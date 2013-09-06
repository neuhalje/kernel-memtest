/*
 * Implement the mmap-interface.
 *
 * Parts of this  code comes from the book "Linux Device
 * Drivers" by Alessandro Rubini and Jonathan Corbet, published
 * by O'Reilly & Associates.
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

#include <linux/init.h>
#include <linux/kernel.h>       /* printk() */
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/mm.h>  /* mmap related stuff */
#include <linux/io.h>  /* virt_to_phys */
#include <linux/errno.h>	/* error codes */
#include <asm/pgtable.h>
#include <linux/semaphore.h>

#include "phys_mem.h"           /* local definitions */
#include "mmap_phys.h"           /* local definitions */
#include "phys_mem_int.h"           /* local definitions */


#define ROUND_UP_TO(x, y)       (((x) + (y) - 1) / (y) * (y))
#define ROUND_UP_TO_PAGE(x)     ROUND_UP_TO((x), PAGE_SIZE)


/*
 * open and close:  keep track of how many times the device is
 * mapped, to avoid releasing it.
 */

void phys_mem_vma_open(struct vm_area_struct *vma)
{
    struct phys_mem_session* session = (struct phys_mem_session*) vma->vm_private_data;

    down(&session->sem);
    session->vmas++;
    up(&session->sem);
}

void phys_mem_vma_close(struct vm_area_struct *vma)
{
  struct phys_mem_session* session = (struct phys_mem_session*) vma->vm_private_data;

  down(&session->sem);
  session->vmas--;

  if (0 == session->vmas)
    SET_STATE(session, SESSION_STATE_CONFIGURED);

  up(&session->sem);
}

struct vm_operations_struct phys_mem_vm_ops = {
	.open =     phys_mem_vma_open,
	.close =    phys_mem_vma_close,
};


int assemble_vma (struct phys_mem_session* session, struct vm_area_struct * vma){
  unsigned long request_iterator;
  int insert_status = 0;

  for (request_iterator = 0; request_iterator < session->num_frame_stati; request_iterator++){
    struct phys_mem_frame_status* frame_status = &session->frame_stati[request_iterator];

    if ( frame_status->page) {
      insert_status  = vm_insert_page(vma,vma->vm_start + frame_status->vma_offset_of_first_byte, frame_status->page);

      if  (unlikely(insert_status)){
        /* Upps! We could not insert our page. This should not really happen, so we just print that
         * and mark it in the configuration.*/
        printk(KERN_WARNING "Could not insert page %p into VMA! Reason: %x", frame_status->page, insert_status);
        frame_status->actual_source |= SOURCE_ERROR_NOT_MAPPABLE;
        goto out;
      }
    }
  }

 out:
  return  insert_status;
}


int file_mmap_configured(struct file * filp, struct vm_area_struct * vma){

   struct phys_mem_session* session = (struct phys_mem_session*) filp->private_data;
   int ret = 0;

   unsigned long  max_size;


    if (down_interruptible (&session->sem))
            return -ERESTARTSYS;

    if ((GET_STATE(session) != SESSION_STATE_CONFIGURED)
        && (GET_STATE(session) != SESSION_STATE_MAPPED) ) {
      ret = -EIO;
      printk(KERN_NOTICE "The session cannot be mmaped in state %i", GET_STATE(session));
      goto err;
    }

    max_size = ROUND_UP_TO_PAGE(SESSION_FRAME_STATI_SIZE(session->num_frame_stati));
    max_size <<= PAGE_SHIFT;

    if ( vma->vm_end - vma->vm_start > max_size){
      ret = -EINVAL;
      printk(KERN_NOTICE "Mmap too large:  %lx > %lx", vma->vm_end - vma->vm_start, max_size );
      goto err;
    }

    ret = assemble_vma(session, vma);
    if (ret)
      goto err;

    vma->vm_ops = &phys_mem_vm_ops;
    vma->vm_flags |= VM_RESERVED;
    vma->vm_flags |= VM_IO;
    vma->vm_private_data = session;

   up(&session->sem);
   phys_mem_vma_open(vma);
   return ret;
err:
  up(&session->sem);
  return ret;

}

