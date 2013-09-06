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
//#include <linux/page-flags.h>
#include <linux/pageblock-flags.h>

#include "phys_mem.h"           /* local definitions */
#include "phys_mem_int.h"           /* local definitions */
#include "page_claiming.h"           /* local definitions */

#ifdef USE_HW_POISON_IMPLEMENTATION_CLONE

#error

int soft_offline_page__clone(struct page *page, int flags);
int unpoison_memory__clone(unsigned long pfn);

inline int try_claim_page_via_hwpoison(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source) {
  if (PageHWPoison(requested_page))
    return CLAIMED_ABORT;

  if(soft_offline_page__clone(requested_page,0))
      return CLAIMED_TRY_NEXT;

  /*
   * soft_offline_page does several things that we do not want
   * - it sets the HW_POISON flag on the page
   * - it increments mce_bad_pages
   */

  *actual_source = SOURCE_HW_POISON;
  return CLAIMED_SUCCESSFULLY;}
#else


// This is reverse-engineered from memory-failure.c
  #ifdef CONFIG_PAGEFLAGS_EXTENDED
     #define IS_COMPUND  ( (1UL << PG_head) | (1UL << PG_tail))
  #else
     #define IS_COMPUND  (1UL << PG_compound)
  #endif

 #define ANY_MUST_BE_SET  ((1UL << PG_lru)|(1UL << PG_unevictable)|(1UL << PG_mlocked))
  #define NONE_MUST_BE_SET  ((1UL << PG_dirty)|IS_COMPUND|(1UL << PG_slab))


static inline bool PageCleanPageCache(struct page* page){
    return ((page->flags & ANY_MUST_BE_SET) && !(page->flags & NONE_MUST_BE_SET));
}
#undef ANY_MUST_BE_SET
#undef NONE_MUST_BE_SET
#undef IS_COMPUND

inline int try_claim_page_via_hwpoison(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source) {

  int ret = CLAIMED_TRY_NEXT;


  bool anon_mandate = PageAnon(requested_page) && (SOURCE_HW_POISON_ANON & allowed_sources );
  bool page_cache_mandate = PageCleanPageCache(requested_page) && (SOURCE_HW_POISON_PAGE_CACHE & allowed_sources );

  bool has_mandate = page_cache_mandate ||  anon_mandate;

  if ( has_mandate ) {
   unsigned long pfn;

  if (PageHWPoison(requested_page))
    return CLAIMED_ABORT;

  my_dump_page(requested_page,"HW-Poison claimer: trying soft_offline_page");

  if(soft_offline_page(requested_page,0))
    {
    my_dump_page(requested_page,"soft-offlined pfn FAILED ");
     return CLAIMED_TRY_NEXT;
    }

  my_dump_page(requested_page,"soft-offlined pfn");

  /* Make sure that I keep the page.
     Unpoisoning decrements the refcount by one.
     If I set it to 2, then I still will own the page.
  */
  atomic_set(&requested_page->_count, 2);

  /*
   FIXME What should I do with the page flags and the other fields of the page?
   */

    pfn = page_to_pfn(requested_page);

    /*
     * soft_offline_page does several things that we do not want
     * - it sets the HW_POISON flag on the page
     * - it increments mce_bad_pages
     */
    if (0 != unpoison_memory(pfn)){
       /* We basically lost a page frame. */
      printk(KERN_NOTICE "Lost pageframe %lux because it could be poisoned but not unpoisoned.\n", pfn);
      ret =  CLAIMED_ABORT;
    }else{
     ret = CLAIMED_SUCCESSFULLY;
     *actual_source = SOURCE_HW_POISON;
    }
  }
  return ret;
}

#endif



