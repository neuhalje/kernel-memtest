/**
 * This module provides the user space direct access to physical memory.
 * In this it mimics the behaviour of /dev/mem.
 *
 * See phys_mem.h for a complete documentation!
 *
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
#include <linux/mm.h>

#include "phys_mem.h"           /* local definitions */
#include "phys_mem_int.h"           /* local definitions */
#include "page_claiming.h"           /* local definitions */


/**
 * These are the methods that the module uses to claim a page.
 */
// try_claim_method try_claim_methods[]  =  {try_claim_free_page,try_claim_free_buddy_page,try_claim_page_in_page_cache,try_claim_page_from_user_process, NULL};
//  try_claim_method try_claim_methods[]  =  {try_claim_free_page,try_claim_free_buddy_page,try_claim_page_in_page_cache,try_claim_page_from_user_process, ignore_difficult_pages,try_claim_page_via_hwpoison,NULL};
//  try_claim_method try_claim_methods[]  =  {try_claim_free_buddy_page,NULL};
try_claim_method try_claim_methods[] = {try_claim_free_buddy_page, ignore_difficult_pages, try_claim_page_via_hwpoison, NULL};
//  try_claim_method try_claim_methods[]  =  {ignore_difficult_pages,try_claim_page_via_hwpoison, try_any_page_claiming, NULL};
//  try_claim_method try_claim_methods[]  =  { NULL};

//#define DEBUG_REQUEST

#ifdef DEBUG_REQUEST
static void dump_request(struct phys_mem_session* session, const struct phys_mem_request* request);
#endif

int handle_mark_page_poison(struct phys_mem_session* session, const struct mark_page_poison* request) {
    int ret = 0;
    unsigned long i;

    if (down_interruptible(&session->sem))
        return -ERESTARTSYS;

    if (unlikely((GET_STATE(session) != SESSION_STATE_MAPPED) &&
            (GET_STATE(session) != SESSION_STATE_CONFIGURED))) {

        printk(KERN_WARNING "Session %llu: The state of the session is invalid: The Request  IOCTL should never appear in state %i\n", session->session_id, GET_STATE(session));

        ret = -EINVAL;
        goto out;
    }

    for (i = 0; i < session->num_frame_stati; i++) {
        struct phys_mem_frame_status * status = &session->frame_stati[i];

        if (status->pfn == request->bad_pfn) {
            if (PFN_IS_CLAIMED(status) && status->page) {
                SetPageHWPoison(status->page);
                printk(KERN_DEBUG "Session %llu: The pfn %lu is now HW_POISONed\n", session->session_id, request->bad_pfn);
                ret = 0;
                goto out;
            }
        } else {
            printk(KERN_DEBUG "Session %llu: The pfn %lu is not claimed for this session\n", session->session_id, request->bad_pfn);
            ret = -EINVAL;
            goto out;
        }
    }


out:
    up(&session->sem);
    return ret;
}

int handle_request_pages(struct phys_mem_session* session, const struct phys_mem_request* request) {
    int ret = 0;
    unsigned long i;

    if (down_interruptible(&session->sem))
        return -ERESTARTSYS;

#ifdef DEBUG_REQUEST
    dump_request(session, request);
#endif

    if (unlikely((GET_STATE(session) != SESSION_STATE_OPEN) &&
            (GET_STATE(session) != SESSION_STATE_CONFIGURED))) {

        if (unlikely(GET_STATE(session) == SESSION_STATE_CONFIGURING))
            /* Depending on the implementation the Session lock could have been temporarily released while configuring.
             */
            printk(KERN_NOTICE "Session %llu: Racy configuring: The Request IOCTL should never appear in state %i\n", session->session_id, GET_STATE(session));
        else
            printk(KERN_WARNING "Session %llu: The state of the session is invalid: The Request  IOCTL should never appear in state %i\n", session->session_id, GET_STATE(session));

        ret = -EINVAL;
        goto out;
    }

    if (GET_STATE(session) == SESSION_STATE_CONFIGURED)
        free_page_stati(session);

    SET_STATE(session, SESSION_STATE_CONFIGURING);

    /*
     * request.req  points to an array of  request.num_requests many
     *  struct phys_mem_frame_request(s) in userspace.
     */
    if (request->num_requests == 0) {
        SET_STATE(session, SESSION_STATE_OPEN);
        goto out;
    }

    session->frame_stati = SESSION_ALLOC_NUM_FRAME_STATI(request->num_requests);
    if (NULL == session->frame_stati) {
        ret = -ENOMEM;
        goto out_to_open;
    }

    memset(session->frame_stati, 0, SESSION_FRAME_STATI_SIZE(request->num_requests));
    session->num_frame_stati = request->num_requests;

    {
        /* Handle all requests */

        /* The VMA maps all successfully mapped pages in the same order as they appear here.
         * To make the users live easier, the relative offset of the frames gets returned in vma_offset_of_first_byte.
         */
        unsigned long current_offset_in_vma = 0;
        struct page * allocated_page;

        u64 jiffies_start, jiffies_end, jiffies_used;

        for (i = 0; i < request->num_requests; i++) {
            struct phys_mem_frame_request __user * current_pfn_request = &request->req[i];

            struct phys_mem_frame_status __kernel * current_pfn_status = &session->frame_stati[i];

            if (copy_from_user(&current_pfn_status->request, current_pfn_request, sizeof (struct phys_mem_frame_request))) {
                printk(KERN_ALERT "Session %llu: Failed to copy_from_user: Request #%lu\n", session->session_id, i);
                ret = -EFAULT;
                goto out_to_open;
            }

            /* current_pfn_status now points to a blank page status
             *
             * Claiming the page is where it gets interesting
             */
            jiffies_start = get_jiffies_64();


            if (unlikely(!pfn_valid(current_pfn_status->request.requested_pfn))) {
                current_pfn_status->actual_source = SOURCE_INVALID_PFN;
                printk(KERN_DEBUG "Session %llu: Invalid pfn: %lu (at position #%lu)\n", session->session_id, current_pfn_status->request.requested_pfn, i);
            } else {
                struct page* requested_page = pfn_to_page(current_pfn_status->request.requested_pfn);

                if (unlikely(NULL == requested_page)) {
                    printk(KERN_NOTICE "Session %llu: Invalid pfn: %lu (at position #%lu): pfn_to_page() returned NULL\n", session->session_id, current_pfn_status->request.requested_pfn, i);
                    ret = -EFAULT;
                    goto out_to_open;
                }

                try_claim_method claim_method = NULL;

                int claim_method_idx = 0;
                int claim_method_result = CLAIMED_TRY_NEXT;

                my_dump_page(requested_page, "Claiming: ");

                /* the claim-method can return a different page, but the default
                 * page is the requested page
                 */
                allocated_page = requested_page;

                /* Iterate each method until a) success or b) failure or c) no more methods */
                while (CLAIMED_TRY_NEXT == claim_method_result) {
                    claim_method = try_claim_methods[claim_method_idx];

                    if (claim_method)
                        claim_method_result = claim_method(requested_page, current_pfn_status->request.allowed_sources, &allocated_page, &current_pfn_status->actual_source);
                    else
                        claim_method_result = CLAIMED_ABORT;

                    claim_method_idx++;
                }

                if (CLAIMED_SUCCESSFULLY == claim_method_result) {

                    current_pfn_status->pfn = page_to_pfn(allocated_page);
                    current_pfn_status->page = allocated_page;
                    current_pfn_status->vma_offset_of_first_byte = current_offset_in_vma;
                    current_offset_in_vma += PAGE_SIZE;
                    printk(KERN_DEBUG "Session %llu: Claimed pfn %lx (requested page is %lx). Method: %lx. Page-Count %i \n", session->session_id, page_to_pfn(requested_page), current_pfn_status->request.requested_pfn, current_pfn_status->actual_source, page_count(requested_page));
                } else {
                    /* Nothing to do*/
                    current_pfn_status->page = NULL;
                    current_pfn_status->pfn = 0;
                    current_pfn_status->vma_offset_of_first_byte = 0;
                    printk(KERN_DEBUG "Session %llu: NOT Claimed pfn %lx (page is for %lx). Method: %lx. Page-Count %i \n", session->session_id, current_pfn_status->request.requested_pfn, page_to_pfn(requested_page), current_pfn_status->actual_source, page_count(requested_page));
                }

            }

            jiffies_end = get_jiffies_64();
            jiffies_used = jiffies_start < jiffies_end ? jiffies_end - jiffies_start : jiffies_start - jiffies_end;
            current_pfn_status->allocation_cost_jiffies = jiffies_used;

        }
    }

    SET_STATE(session, SESSION_STATE_CONFIGURED);

out:
    up(&session->sem);
    return ret;

out_to_open:
    printk(KERN_NOTICE "The Request IOCTL could not be completed!\n");
    free_page_stati(session);

    SET_STATE(session, SESSION_STATE_OPEN);

    up(&session->sem);
    return ret;
}


#ifdef DEBUG_REQUEST

static void dump_request(struct phys_mem_session* session, const struct phys_mem_request* request) {
    long int index = 0;
    if (!request)
        return;

    printk(KERN_DEBUG "Session %llu :Dumping %lu requested pages at %p:\n", session->session_id, request->num_requests, request->req);

    if (request->req) {
        for (index = 0; index < request->num_requests; index++) {
            // request->req is of type __user
            long pfn, allowed_sources;
            get_user(pfn, &request->req[index].requested_pfn);
            get_user(allowed_sources, &request->req[index].allowed_sources);

            printk(KERN_DEBUG "Session %llu: pfn %lu %lx \n", session->session_id, pfn, allowed_sources);
        }
    } else {
        printk(KERN_NOTICE "Session %llu: Dumping %lu requested pages: No Data\n", session->session_id, request->num_requests);
    }

    printk(KERN_DEBUG "Session %llu: DONE Dumping %lu requested pages:\n", session->session_id, request->num_requests);

}

#endif
