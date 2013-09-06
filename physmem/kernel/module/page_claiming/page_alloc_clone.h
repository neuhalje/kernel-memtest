/*
 * page_alloc_clone.h
 *
 * Contains method definitions for methods copied/adapted
 * from the buddy subsystem (page_alloc.c)
 */

#ifndef PAGE_ALLOC_CLONE_H_
#define PAGE_ALLOC_CLONE_H_


 inline unsigned long page_order__clone(struct page *page);
 inline void rmv_page_order__clone(struct page *page);


//static inline int check_new_page(struct page *page);
 inline void expand__clone(struct zone *zone, struct page *page,
        int low, int high, struct free_area *area,
        int migratetype);

 inline int get_pageblock_migratetype__clone(struct page *page);


#endif /* PAGE_ALLOC_CLONE_H_ */
