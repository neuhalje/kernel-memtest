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

/**
 * This module provides the user space direct access to physical memory.
 * In this it mimics the behaviour of /dev/mem.
 *
 * See phys_mem.h for a complete documentation!
 *
 *
 */

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/init.h>
#include <linux/kernel.h>       /* printk() */
#include <linux/errno.h>        /* error codes */
#include <linux/mm.h>
#include <linux/pageblock-flags.h>

#include <asm-generic/sections.h> /* _end */
#include <asm/io.h>

#include "phys_mem_int.h"           /* local definitions */
#include "page_claiming.h"           /* local definitions */



#define pfn(address) page_to_pfn(virt_to_page( ((void*)(address)) ) )


/**
 * Ignore pages that are known to be "untestable". Touching certain pages may lead to kernel crashes or other
 * undesirable effects. This implementation ABORTs the freeing process for these pages.
 *
 */
int ignore_difficult_pages(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source) {
  int ret = CLAIMED_TRY_NEXT;

   unsigned long requested_pfn = page_to_pfn(requested_page);

   unsigned int is_first_mb = (page_to_phys(requested_page) <= 0x400 );
   // _end is not exported
//   unsigned int is_kernel_code = (requested_pfn <= pfn(_end));
   unsigned int is_kernel_code =  (page_to_phys(requested_page) <= 0x800 ) && !is_first_mb;

   if (is_first_mb || is_kernel_code)
     ret = CLAIMED_ABORT;

   return ret;
}
