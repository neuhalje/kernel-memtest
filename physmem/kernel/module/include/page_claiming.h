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


#ifndef PAGE_CLAIMING_H_
#define PAGE_CLAIMING_H_

/**
 * Implements the Request-Pages command
 *
 * The function is called with the session semaphore NOT held and has to
 * take care of this.
 *
 * The tasks of handle_request_pages are:
 *
 * 1) Set the session state to 'Configuring'
 * 2) Allocate and populate the Frame.-stati via SESSION_ALLOC_NUM_FRAME_STATI(n)
 * 3) Try to claim all pages requested
 * 4) Set the session state to 'Configured'
 *
 * OR
 *
 * x) Set the state to 'Open' (error case) and clean up the mess
 *
 */
int handle_request_pages(struct phys_mem_session*, const struct phys_mem_request*);

int handle_mark_page_poison(struct phys_mem_session* session, const struct mark_page_poison* request);

#define CLAIMED_SUCCESSFULLY 1 /* The page had been claimed and all is well.*/
#define CLAIMED_TRY_NEXT     2 /* The page could not be claimed because this function is not responsible for it. Try the next mechanism. */
#define CLAIMED_ABORT        3 /* Abort processing, the page could not be claimed. */

/**
 * Prototype for a page-claiming mechanism.
 *
 * Returns CLAIMED_*
 *
 * Iff CLAIMED_SUCCESSFULLY is returned, then *actual_source should be updated.
 */
typedef int (*try_claim_method)(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);


int try_claim_page_from_user_process(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);
int try_claim_page_in_page_cache(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);
int try_claim_free_page(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);
int try_claim_free_buddy_page(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);

int try_claim_page_via_hwpoison(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);

int try_any_page_claiming(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page,  unsigned long* actual_source);

int ignore_difficult_pages(struct page* requested_page, unsigned int allowed_sources,struct page** allocated_page, unsigned long* actual_source);

void my_dump_page(struct page* page, char* msg);

#endif /* PAGE_CLAIMING_H_ */
