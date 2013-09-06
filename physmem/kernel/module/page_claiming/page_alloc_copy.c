/**
 * This file is (more or less) a copy of page_alloc.c
 *
 * (Nearly) all functions are static or stripped by the
 * kernel build process. This leads to link-errors and prevents the
 * module from being loaded.
 *
 * Removing specific pages from the buddy system is NOT supported by
 * Linux, so the buddy allocator had to be reverse engineered
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

#include "page_alloc_clone.h"           /* local definitions */

static inline void set_page_order__clone(struct page *page, int order);
static inline unsigned long get_pageblock_flags_group__clone(struct page *page,
                                       int start_bitidx, int end_bitidx);

//
///*
// * This is a modified version of  'buffered_rmqueue' from page_alloc.c
// *
// *
// *
// * The original version tried to allocate some pages from a zone.
// * This version directly goes for a single page
// *
// * struct zone *preferred_zone,
// * struct zone *zone,
// * int order,
// * gfp_t gfp_flags,
// * int migratetype
// */
//static inline
//struct page *buffered_rmqueue(
//                        struct page* requested_page,
//                        struct zone *preferred_zone,
//                         int order, gfp_t gfp_flags,
//                        int migratetype)
//{
//        unsigned long flags;
//        struct page *page;
//        int cold = !!(gfp_flags & __GFP_COLD);
//        int cpu;
//
//        // Params
//        int order = 0;
//        requested_page->
//
//
//again:
//        cpu  = get_cpu();
//        if (likely(order == 0)) {
//                struct per_cpu_pages *pcp;
//                struct list_head *list;
//
//                pcp = &zone_pcp(zone, cpu)->pcp;
//                list = &pcp->lists[migratetype];
//                local_irq_save(flags);
//                if (list_empty(list)) {
//                        pcp->count += rmqueue_bulk(zone, 0,
//                                        pcp->batch, list,
//                                        migratetype, cold);
//                        if (unlikely(list_empty(list)))
//                                goto failed;
//                }
//
//                if (cold)
//                        page = list_entry(list->prev, struct page, lru);
//                else
//                        page = list_entry(list->next, struct page, lru);
//
//                list_del(&page->lru);
//                pcp->count--;
//        } else {
//                if (unlikely(gfp_flags & __GFP_NOFAIL)) {
//                        /*
//                         * __GFP_NOFAIL is not to be used in new code.
//                         *
//                         * All __GFP_NOFAIL callers should be fixed so that they
//                         * properly detect and handle allocation failures.
//                         *
//                         * We most definitely don't want callers attempting to
//                         * allocate greater than order-1 page units with
//                         * __GFP_NOFAIL.
//                         */
//                        WARN_ON_ONCE(order > 1);
//                }
//                spin_lock_irqsave(&zone->lock, flags);
//                page = __rmqueue(zone, order, migratetype);
//                spin_unlock(&zone->lock);
//                if (!page)
//                        goto failed;
//                __mod_zone_page_state(zone, NR_FREE_PAGES, -(1 << order));
//        }
//
//        __count_zone_vm_events(PGALLOC, zone, 1 << order);
//        zone_statistics(preferred_zone, zone);
//        local_irq_restore(flags);
//        put_cpu();
//
//        VM_BUG_ON(bad_range(zone, page));
//        if (prep_new_page(page, order, gfp_flags))
//                goto again;
//        return page;
//
//failed:
//        local_irq_restore(flags);
//        put_cpu();
//        return NULL;
//}
/* Stolen from: linux/mm/internal.h
 *
 *
 * function for dealing with page's order in buddy system.
 * zone->lock is already acquired when we use these.
 * So, we don't need atomic page->flags operations here.
 */
 inline unsigned long page_order__clone(struct page *page)
{
        VM_BUG_ON(!PageBuddy(page));
        return page_private(page);
}

/* Stolen from: mm/page_alloc.c
 *
 */
 inline void rmv_page_order__clone(struct page *page)
{
        __ClearPageBuddy(page);
        set_page_private(page, 0);
}



#ifdef CONFIG_DEBUG_VM
/* Stolen from: mm/page_alloc.c
 */
static int page_outside_zone_boundaries(struct zone *zone, struct page *page)
{
        int ret = 0;
        unsigned seq;
        unsigned long pfn = page_to_pfn(page);

        do {
                seq = zone_span_seqbegin(zone);
                if (pfn >= zone->zone_start_pfn + zone->spanned_pages)
                        ret = 1;
                else if (pfn < zone->zone_start_pfn)
                        ret = 1;
        } while (zone_span_seqretry(zone, seq));

        return ret;
}
/* Stolen from: mm/page_alloc.c
 */
static int page_is_consistent(struct zone *zone, struct page *page)
{
        if (!pfn_valid_within(page_to_pfn(page)))
                return 0;
        if (zone != page_zone(page))
                return 0;

        return 1;
}
/* Stolen from: mm/page_alloc.c
 *
 * Temporary debugging check for pages not lying within a given zone.
 */
static int bad_range(struct zone *zone, struct page *page)
{
        if (page_outside_zone_boundaries(zone, page))
                return 1;
        if (!page_is_consistent(zone, page))
                return 1;

        return 0;
}
#else
/* Stolen from: mm/page_alloc.c
 */
static inline int bad_range(struct zone *zone, struct page *page)
{
        return 0;
}
#endif


/* Stolen from: mm/page_alloc.c
 *
 * The order of subdivision here is critical for the IO subsystem.
 * Please do not alter this order without good reasons and regression
 * testing. Specifically, as large blocks of memory are subdivided,
 * the order in which smaller blocks are delivered depends on the order
 * they're subdivided in this function. This is the primary factor
 * influencing the order in which pages are delivered to the IO
 * subsystem according to empirical testing, and this is also justified
 * by considering the behavior of a buddy system containing a single
 * large block of memory acted on by a series of small allocations.
 * This behavior is a critical factor in sglist merging's success.
 *
 * -- wli
 */
 inline void expand__clone(struct zone *zone, struct page *page,
        int low, int high, struct free_area *area,
        int migratetype)
{
        unsigned long size = 1 << high;

        while (high > low) {
                area--;
                high--;
                size >>= 1;
                VM_BUG_ON(bad_range(zone, &page[size]));
                list_add(&page[size].lru, &area->free_list[migratetype]);
                area->nr_free++;
                set_page_order__clone(&page[size], high);
        }
}
/* Stolen from: mm/page_alloc.c
*/
static inline void set_page_order__clone(struct page *page, int order)
{
        set_page_private(page, order);
        __SetPageBuddy(page);
}

///* Stolen from: mm/page_alloc.c
// *
// * This page is about to be returned from the page allocator
// */
//static inline int check_new_page(struct page *page)
//{
//        if (unlikely(page_mapcount(page) |
//                (page->mapping != NULL)  |
//                (atomic_read(&page->_count) != 0)  |
//                (page->flags & PAGE_FLAGS_CHECK_AT_PREP))) {
//                bad_page(page);
//                return 1;
//        }
//        return 0;
//}
//
///* Stolen from: mm/page_alloc.c
//*/
//static void bad_page(struct page *page)
//{
//        static unsigned long resume;
//        static unsigned long nr_shown;
//        static unsigned long nr_unshown;
//
//        /* Don't complain about poisoned pages */
//        if (PageHWPoison(page)) {
//                __ClearPageBuddy(page);
//                return;
//        }
//
//        /*
//         * Allow a burst of 60 reports, then keep quiet for that minute;
//         * or allow a steady drip of one report per second.
//         */
//        if (nr_shown == 60) {
//                if (time_before(jiffies, resume)) {
//                        nr_unshown++;
//                        goto out;
//                }
//                if (nr_unshown) {
//                        printk(KERN_ALERT
//                              "BUG: Bad page state: %lu messages suppressed\n",
//                                nr_unshown);
//                        nr_unshown = 0;
//                }
//                nr_shown = 0;
//        }
//        if (nr_shown++ == 0)
//                resume = jiffies + 60 * HZ;
//
//        printk(KERN_ALERT "BUG: Bad page state in process %s  pfn:%05lx\n",
//                current->comm, page_to_pfn(page));
//        printk(KERN_ALERT
//                "page:%p flags:%p count:%d mapcount:%d mapping:%p index:%lx\n",
//                page, (void *)page->flags, page_count(page),
//                page_mapcount(page), page->mapping, page->index);
//
//        dump_stack();
//out:
//        /* Leave bad fields for debug, except PageBuddy could make trouble */
//        __ClearPageBuddy(page);
//        add_taint(TAINT_BAD_PAGE);
//}
/* Stolen from: mm/page_alloc.c
 * Made a clone (different name) because the compiler would find the original function - but
 * the linker won't.
 * **/
 inline int get_pageblock_migratetype__clone(struct page *page)
{
        return get_pageblock_flags_group__clone(page, PB_migrate, PB_migrate_end);
}

/* Stolen from: mm/page_alloc.c
*/
 inline int pfn_to_bitidx__clone(struct zone *zone, unsigned long pfn)
{
#ifdef CONFIG_SPARSEMEM
        pfn &= (PAGES_PER_SECTION-1);
        return (pfn >> pageblock_order) * NR_PAGEBLOCK_BITS;
#else
        pfn = pfn - zone->zone_start_pfn;
        return (pfn >> pageblock_order) * NR_PAGEBLOCK_BITS;
#endif /* CONFIG_SPARSEMEM */
}


/* Return a pointer to the bitmap storing bits affecting a block of pages
 *  Stolen from: mm/page_alloc.c
 */
 inline unsigned long *get_pageblock_bitmap__clone(struct zone *zone,
                                                        unsigned long pfn)
{
#ifdef CONFIG_SPARSEMEM
        return __pfn_to_section(pfn)->pageblock_flags;
#else
        return zone->pageblock_flags;
#endif /* CONFIG_SPARSEMEM */
}

/* Stolen from: mm/page_alloc.c
 *
 * Made a clone (different name) because the compiler would find the original function - but
 * the linker won't.
 *
 * get_pageblock_flags_group - Return the requested group of flags for the pageblock_nr_pages block of pages
 * @page: The page within the block of interest
 * @start_bitidx: The first bit of interest to retrieve
 * @end_bitidx: The last bit of interest
 * returns pageblock_bits flags
 */
 static inline unsigned long get_pageblock_flags_group__clone(struct page *page,
                                        int start_bitidx, int end_bitidx)
{
        struct zone *zone;
        unsigned long *bitmap;
        unsigned long pfn, bitidx;
        unsigned long flags = 0;
        unsigned long value = 1;

        zone = page_zone(page);
        pfn = page_to_pfn(page);
        bitmap = get_pageblock_bitmap__clone(zone, pfn);
        bitidx = pfn_to_bitidx__clone(zone, pfn);

        for (; start_bitidx <= end_bitidx; start_bitidx++, value <<= 1)
                if (test_bit(bitidx + start_bitidx, bitmap))
                        flags |= value;

        return flags;
}
