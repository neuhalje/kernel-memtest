/*
    Copyright (C) 2010  Jens Neuhalfen -- Some functions have been extracted from
    the Linux kernel. These have been noted as such.

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
#include <linux/fs.h>           /* everything... */
#include <linux/errno.h>        /* error codes */
#include <linux/types.h>        /* size_t */
#include <linux/fcntl.h>        /* O_ACCMODE */
#include <asm/uaccess.h>
#include <linux/mm.h>
//#include <linux/page-flags.h>
#include <linux/pageblock-flags.h>

#include "phys_mem.h"           /* local definitions */
#include "phys_mem_int.h"           /* local definitions */
#include "page_claiming.h"           /* local definitions */


/*
 *  Like "free_pages_check", only without calling bad_page/modifying the
 *  page.
 */
static inline int free_pages_check__just_test(struct page *page)
{
        if (unlikely(page_mapcount(page) |
                (page->mapping != NULL)  |
                (atomic_read(&page->_count) != 0) |
                (page->flags & PAGE_FLAGS_CHECK_AT_FREE))) {
                return 1;
        }
        return 0;
}


/**
 * Try to claim a "free" page that is neither in the buddy system nor somewhere else
 *
 * This is currently disabled because it is virtually impossible to detect, if a page
 * is free in the described way.
 *
 * To quote from memory-failure.c
 *
 *       * We need/can do nothing about count=0 pages.
         * 1) it's a free page, and therefore in safe hand:
         *    prep_new_page() will be the gate keeper.
         * 2) it's part of a non-compound high order page.
         *    Implies some kernel user: cannot stop them from
         *    R/W the page; let's pray that the page has been
         *    used and will be freed some time later.
         * In fact it's dangerous to directly bump up page count from 0,
         * that may make page_freeze_refs()/page_unfreeze_refs() mismatch.
 *
 */
inline int try_claim_free_page(struct page* requested_page, unsigned int allowed_sources, struct page** allocated_page, unsigned long* actual_source) {
  int ret = CLAIMED_TRY_NEXT;

  int enabled = 0;

   if ( enabled && (allowed_sources & SOURCE_FREE_PAGE)) {
     struct page* compound_head_page;

       compound_head_page = compound_head(requested_page);

       /*
        * This is a heuristic: Normally all pages should be 'somewhere', so this is very likely to be 'false' for all pages
        *
        * Additionally this test is propably not correct anyway.
        * */
       if (compound_head_page == requested_page
            &&  !free_pages_check__just_test(requested_page) == 0
            && requested_page->lru.next == NULL && requested_page->lru.prev == NULL) {


            int locked_page_count_before, locked_page_count_after;

            locked_page_count_before = page_count(requested_page);
            get_page(requested_page);

            if (requested_page){
              /*
               * The page is now rightfully ours!
               */
              locked_page_count_after = page_count(requested_page);


                printk(KERN_DEBUG "Requested pfn %lx  with pagecount %i (was:%i)\n", page_to_pfn(requested_page),  locked_page_count_after, locked_page_count_before);
                *actual_source = SOURCE_FREE_PAGE;
                ret =  CLAIMED_SUCCESSFULLY;
              }else{
                /**
                 * We could not lock the page
                 */
                printk(KERN_DEBUG "Requested pfn %lx but could not get it though it was _count == 0.)\n", page_to_pfn(requested_page));
              }
           }
   }
   return ret;
}

