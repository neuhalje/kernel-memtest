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
 * In this it mimics the behaviour of /dev/mem. Contrary to /dev/mem the
 * module has a different use case: /dev/mem  allows direct access to any
 * memory location, inviting a malicious user to wreak havoc on the system
 * by overwriting important structures or reading secret data.
 *
 * This module works different:
 *
 *   The user configures a set of page frames to be prepared for
 *      later mmaping.
 *
 *   The module tries to get a hold of the requested frames (struct page).
 *      In no case the user process may access pages that are not reserved
 *      for this process.
 *      Reserved memory can then be mmapped by the user process.
 *
 * Usage
 * ======
 *
 * 1) Open the device.
 *
 * 2) Use the 'Request'-IOCTL to pass the list of requested
 *    frame numbers to the driver. The driver will then try
 *    to claim the requested pages.
 *    The order of requested frames does matter: When the user requests
 *    the pfns 1,2,3,10 the module will provide a vma that puts pfn 2 between
 *    1 and 3 and 3 between 2 and 10. See step 3 for details.
 *
 *
 * 3) Use the 'Query status' IOCTL to query for the status of the request.
 *    This ioctl will provide with everything you need to know for the next
 *    step. For each requested physical frame, the following properties will
 *    be returned:
 *      - The requested PFN
 *      - The status of the PFN: Claimed (ready for use) or Unclaimed (the
 *        module could/would not claim this frame).
 *      - The means, by which this frame has been claimed. Had it been free,
 *        in the page cache or somewhere different altogether?
 *      - The first and last address of the frame in the VMA
 *        (virtual __user address)
 *
 *         *
 *    Example (requesting 1,2,3,10):
 *
 *    pfn  |  virtual start..end | (more)
 *    -----+---------------------+-------
 *     1   |     0.. 4095   <-- Each line is a Pagestatus
 *     2   |  4096.. 8191
 *     3   |  8192..12287
 *    10   | 12288..16383
 *
 *   When the module cannot claim a page, the page will not be included
 *   in the vma:
 *
 *    Example (requesting 1,2,3,10 & the module could not get pfn 3):
 *
 *    pfn  |  virtual start..end
 *    -----+--------------------
 *     1   |     0.. 4095
 *     2   |  4096.. 8191
 *    10   |  8192..12287
 *
 * 4) mmap the region. The size of the region is 0..end of last frame. In
 *    the case depicted above: 0..16383 / 0..12287
 *    The flags O_DIRECT and O_SYNC from the Open call are used here.
 *
 *
 * Each call to "open" creates a new session.
 * The state chart for a session looks like this:
 *
 *
 *                             .--- [Request] ----.
 *                             \/                 |
 *        .-[Request] --> CONFIGURING             |
 *        |                    .---------------.  |   .-[ Query status] -.
 *        .------------.                       \/ |   \/                 |
 *                     |                      CONFIGURED >---------------.
 *                     |                         /\  |
 * CLOSED --[open]--> OPEN                       |   |
 *                                               |  [mmap]
 *                                           [unmap] |
 *                                               |   |   .-------------------.
 *                                               |   \/  \/                  |
 *                                               MAPPED >---[ Query status ]-.
 *
 *
 * State changes to "CLOSED" are not depicted. Mapping a second time (while
 * there is already a mapping) is allowed. The step to CONFIGURED is done
 * after last mmap has been unmapped.
 *
 *
 * Implementation (static)
 * =======================
 *
 *
 *  Device 1--n Session 1----------------------------------------------n vma
 *              1 |                                                      | m
 *                |                                                      |
 *                | 0..1                                                 | n
 *       Configuration 1---[0..1] Status  -- n Pagestatus -- [0.1] struct Page*
 *                  | 1                               | 1
 *             0..1 |                                 |
 *                Request  1 -------------------------.
 *
 *  Each device is associated with several sessions.
 *
 *  A session correlates to an open file (via filp->private_data).
 *
 *  The session configuration contains the users Request
 *    and the Status that can be queried via 'Query status'.
 *
 *  The status itself contains one Pagestatus per requested physical frame.
 *
 *  A mapped vma then holds a pointer to the Session and implements the mapping
 *  described in the Pagestatus-Objects.
 *
 * Locks
 * =====
 *  - The "device lock" protects the device.
 *  - The "session lock" protects the session, the configuration, the request
 *    and the status with all pagestati.
 *
 *
 * Implementation (dynamic)
 * =======================
 *
 * CLOSED:
 * ----------
 *
 *    The session is not existing.
 *
 * CLOSED -> OPEN:
 * ---------------
 *
 *   Trigger: Opening the file.
 *
 *   Locks:
 *         - the device lock will be held during the transition
 *
 *   Opening the device via 'file::open' creates the session object and
 *   associates it with the "struct file*".
 *
 * OPEN -> CONFIGURING:
 * ----------------------
 *
 *   Trigger: Issuing a valid 'Request' IOCTL
 *
 *   Locks:
 *         - the device lock will be held during the transition
 *         - the session lock will be created
 *
 *   The Configuration is updated with the request and the page-claiming
 *   process starts.
 *
 *   CONFIGURING is an internal state that should not be visible from the
 *   client. Multitasking allows for several sessions in the CONFIGURING
 *   state though.
 *
 *   After the pages have been claimed and the Pagestati have been updated
 *   the state shifts to CONFIGURED.
 *
 * CONFIGURING -> CONFIGURED:
 * ----------------------------
 *
 *   Trigger: The request has been processed. This is an internal step.
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 *   The session is now ready for 'Query status' and mmaping. A configured
 *   (but not mmapped) session can be reconfigured.
 *
 * CONFIGURED -> CONFIGURING:
 * ----------------------------
 *
 *   Trigger: Issuing a valid 'Request' IOCTL
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 *   All  pages that were allocated upon the former request are freed and
 *   the pagestati are removed.
 *
 *   The new internal status is effectively set to that of the OPEN-state.
 *
 *   @see OPEN -> CONFIGURING
 *
 * CONFIGURED -> CONFIGURED:
 * ----------------------------
 *
 *   Trigger: The user issues a valid 'Request status' request
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 *
 * CONFIGURED -> MAPPED:
 * ----------------------------
 *
 *   Trigger: The user issues a valid 'mmap' request
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 *   When a user process issues an mmap call against a configured file object,
 *   the module creates the VMA according to the Status object.
 *
 * MAPPED -> MAPPED (mmap):
 * ----------------------------
 *
 *   Trigger: The user issues a valid 'mmap' request
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 *   When a user process issues an mmap call against a configured file object,
 *   the module creates the VMA according to the Status object.
 *
 * MAPPED -> MAPPED (Query status):
 * ----------------------------
 *
 *   Trigger: The user issues a valid 'Request status' request
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 * MAPPED -> MAPPED (munmap):
 * ----------------------------
 *
 *   Trigger: The user issues a valid 'munmap' request, there are other open
 *            VMAs for this session.
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 *
 * MAPPED -> CONFIGURED (munmap):
 * ----------------------------
 *
 *   Trigger: The user issues a valid 'munmap' request and there is no other
 *            open VMA for this session.
 *
 *   Locks:
 *         - the session lock will be held during the transition
 *
 * [ANY] -> CLOSED
 * ----------------------------
 *
 *   Trigger: The user closes the file handle or the process terminates.
 *
 *   Locks:
 *         - the session lock will be held and destroyed during the transition
 *         - the device lock will be held during the transition
 *
 *   The kernel takes care of unmapping all VMAs. This transition frees all
 *   claimed pages and destroys the session object.
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

#ifndef PHYS_MEM__H_
#define PHYS_MEM__H_

#include <linux/ioctl.h>


#define PHYS_MEM_MAJOR 0   /* dynamic major by default. 0 == dynamic allocation of the major  number */


#define SOURCE_FREE_PAGE          0x00001       /* Use the 'Free Pages' Claimer (currently disabled) */
#define SOURCE_FREE_BUDDY_PAGE    0x00002       /* Use the 'Free Buddy' Claimer: Use a free page associated with the buddy system */

#define SOURCE_PAGE_CACHE         0x00004      /* Use the  'wrest a page from the page cache'-claimer */
#define SOURCE_ANONYMOUS          0x00008       /* Use the  'steal the page from a user process' claimer  */

#define SOURCE_ANY_PAGE           0x00010       /* Let the module decide */

#define SOURCE_HW_POISON_ANON         0x00020       /* Use the HW_POISON claimer */
#define SOURCE_HW_POISON_PAGE_CACHE          0x00040       /* Use the HW_POISON claimer */
#define SOURCE_HW_POISON          (SOURCE_HW_POISON_ANON |  SOURCE_HW_POISON_PAGE_CACHE)


#define SOURCE_INVALID_PFN        0x80000       /* Not a source but the reply for invalid (too large) PFNs */

#define SOURCE_ERROR_NOT_MAPPABLE        0x100000       /* Failed to insert Page in VMA */

#define SOURCE_MASK             0x000FFFFF
#define SOURCE_ERROR_MASK       0xFFF00000

#define PFN_IS_CLAIMED(phys_mem_frame_status) ((phys_mem_frame_status->actual_source & SOURCE_MASK) != 0)
/**
 * A single request for a single pfn
 */
struct phys_mem_frame_request {
   unsigned   long requested_pfn;
   unsigned  long allowed_sources; /* Bitmask of SOURCE_* */
};

/**
 * The status of a pfn
 */
struct phys_mem_frame_status {
   struct phys_mem_frame_request        request;
   unsigned long long                        vma_offset_of_first_byte;      /* A pointer to the first byte of the frame, relative to the start of the VMA */
   unsigned  long                              pfn;                    /* The pfn of the frame */
   unsigned long long                                  allocation_cost_jiffies;       /* How long did it take to get a hold on this frame? Measured in jiffies*/
   unsigned  long                       actual_source;                 /* A single item of SOURCE_* (optionally ORed with one SOURCE_ERROR_**/
   struct page*                         page;                          /* The claimed (get_page) page describing this pfn OR NULL, when the page could not be claimed */
};



/*
 * The different configurable parameters
 */
extern int phys_mem_major;     /* main.c */
extern int phys_mem_devs;
extern int phys_mem_order;
extern int phys_mem_qset;



/*
 * Ioctl definitions
 */


#define IOCTL_REQUEST_VERSION   1

struct phys_mem_request {
  unsigned  long protocol_version; /* The protocol/struct version of this IOCTL call. Must be IOCTL_REQUEST_VERSION */
  unsigned  long num_requests;     /* The number of frame requests */
  struct phys_mem_frame_request   *req; /* A pointer to the array of requests. The array must contain at least num_requests items */
};

struct mark_page_poison{
  unsigned  long protocol_version; /* The protocol/struct version of this IOCTL call. Must be IOCTL_REQUEST_VERSION */
  unsigned  long bad_pfn;     /* The bad pfn */
};


/* Use 'K' as magic number */
#define PHYS_MEM_IOC_MAGIC  'K'

/**
 * The 'Configure' IOCTL described above.
 */
#define PHYS_MEM_IOC_REQUEST_PAGES    _IOW(PHYS_MEM_IOC_MAGIC, 0, struct phys_mem_request )
#define PHYS_MEM_IOC_MARK_FRAME_BAD    _IOW(PHYS_MEM_IOC_MAGIC, 1, struct mark_page_poison )


#define PHYS_MEM_IOC_MAXNR 1

#endif
