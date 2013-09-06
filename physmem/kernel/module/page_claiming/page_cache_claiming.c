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
#include <linux/mm.h>

#include "phys_mem.h"           /* local definitions */
#include "phys_mem_int.h"           /* local definitions */
#include "page_claiming.h"           /* local definitions */



/**
 * Try to claim page from the page-cache
 */
int try_claim_page_in_page_cache(struct page* requested_page, unsigned int allowed_sources, struct page** allocated_page, unsigned long* actual_source) {
  int ret = CLAIMED_TRY_NEXT;

  if ( allowed_sources & SOURCE_PAGE_CACHE) {
    /* FIXME Moved to HW-Poison*/
  }
  return ret;
}


