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

#ifndef PHYS_MEM_INT_H_
#define PHYS_MEM_INT_H_

#include <linux/ioctl.h>
#include <linux/cdev.h>
#include <linux/vmalloc.h>
#include <linux/semaphore.h>

#include "phys_mem.h"


struct phys_mem_dev {
        struct phys_mem_dev *next;  /* next listitem */
        struct semaphore sem;     /* Mutual exclusion */
        struct cdev cdev;
};


/**
 * The states of the Session-Statemachine
 */

#define SESSION_STATE_CLOSED         0
#define SESSION_STATE_OPEN           1
#define SESSION_STATE_CONFIGURING    2
#define SESSION_STATE_CONFIGURED     3
#define SESSION_STATE_MAPPED         4

#define SESSION_STATE_INVALID        5

/* Legal states */
#define SESSION_NUM_STATES           5



#define GET_STATE(session) ((session)->status.state)
#define SET_STATE(session,value) set_state((session),(value))

struct session_status {
  unsigned int state;
};



/**
 * A session as described at the top of the file
 */
struct phys_mem_session {
         struct session_status status;
         unsigned long long    session_id;
         int vmas;                              /* active mappings */
         struct phys_mem_dev *  device;
         struct semaphore       sem;            /* Session Lock */
         unsigned long          num_frame_stati;     /* The number of frame stati in status */
         struct phys_mem_frame_status* frame_stati; /* An array with num_status items */
};

extern struct phys_mem_dev *phys_mem_devices;



/*
 * Internal functions / global variables
 */




/**
 * Free the page stati of a session. Also release any page reference found in there.
 *
 * The function must be called with the session lock held!
 */
void free_page_stati(struct phys_mem_session* session);

/**
 * The size of a number of frame-stati
 */
#define     SESSION_FRAME_STATI_SIZE(num)  (num) * sizeof(struct phys_mem_frame_status)

/**
 * Allocating and freeing memory for the frame-stati (session.frame_stati)
 */
#define     SESSION_FREE_FRAME_STATI(p) vfree(p)
#define     SESSION_ALLOC_NUM_FRAME_STATI(num) vmalloc( SESSION_FRAME_STATI_SIZE(num) )


extern struct file_operations phys_mem_fops;
extern struct kmem_cache *session_mem_cache;

static char * SESSION_STATE_TXT[] = {
    "SESSION_STATE_CLOSED",
    "SESSION_STATE_OPEN",
    "SESSION_STATE_CONFIGURING",
    "SESSION_STATE_CONFIGURED",
    "SESSION_STATE_MAPPED",
    "- INVALID -"
};

static inline void set_state(struct phys_mem_session * session,  unsigned int new_state){
  if (new_state >= SESSION_NUM_STATES)
    new_state = SESSION_STATE_INVALID;

  printk(KERN_DEBUG "Session %llu: %s -> %s\n",session->session_id, SESSION_STATE_TXT[GET_STATE(session)], SESSION_STATE_TXT[new_state]) ;

  session->status.state = new_state;
}

#endif /* PHYS_MEM_INT_H_ */
