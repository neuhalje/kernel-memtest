#ifdef USE_HW_POISON_IMPLEMENTATION_CLONE

/*
 * This is a stripped down version of mm/internal.h
 *
 * It has been extracted from kernel 2.6.34-rc2
 *
 * Some Kernels  do not support HW-Poison. The implementation of
 * the HW-Poison code is still usefull though.
 *
 * Instead of reinventing the wheel multiple times,
 * this C module follows the HW-Poison implementation
 * very close, thus allowing patches to be applied very
 * efficient.
 *
 */


/* internal.h: mm/ internal definitions
 *
 * Copyright (C) 2004 Red Hat, Inc. All Rights Reserved.
 * Written by David Howells (dhowells@redhat.com)
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version
 * 2 of the License, or (at your option) any later version.
 */
#ifndef __MM_INTERNAL_CLONE_H
#define __MM_INTERNAL__CLONE_H

#include <linux/mm.h>

/*
 * function for dealing with page's order in buddy system.
 * zone->lock is already acquired when we use these.
 * So, we don't need atomic page->flags operations here.
 */
static inline unsigned long page_order(struct page *page)
{
	VM_BUG_ON(!PageBuddy(page));
	return page_private(page);
}
/*
 * in mm/vmscan.c:
 */
extern int isolate_lru_page(struct page *page);
extern void putback_lru_page(struct page *page);

#endif
#endif
