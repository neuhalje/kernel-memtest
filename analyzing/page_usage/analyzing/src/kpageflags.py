'''
This source code is distributed under the MIT License

Copyright (c) 2010, Jens Neuhalfen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

"""
 Pageflags taken from <Kernel>/Documentation/vm/pagemap.txt
 Transformed via
 s/^[ ]\+\([0-9]\+\)\.[ ]\+\([^ ]\+\)/\2\t=\t1 << \1/gc




 * /proc/kpageflags.  This file contains a 64-bit set of flags for each
   page, indexed by PFN.

   The flags are (from fs/proc/page.c, above kpageflags_read):

     0. LOCKED
     1. ERROR
     2. REFERENCED
     3. UPTODATE
     4. DIRTY
     5. LRU
     6. ACTIVE
     7. SLAB
     8. WRITEBACK
     9. RECLAIM
    10. BUDDY
    11. MMAP
    12. ANON
    13. SWAPCACHE
    14. SWAPBACKED
    15. COMPOUND_HEAD
    16. COMPOUND_TAIL
    16. HUGE
    18. UNEVICTABLE
    19. HWPOISON
    20. NOPAGE
    21. KSM

Short descriptions to the page flags:

 0. LOCKED
    page is being locked for exclusive access, eg. by undergoing read/write IO

 7. SLAB
    page is managed by the SLAB/SLOB/SLUB/SLQB kernel memory allocator
    When compound page is used, SLUB/SLQB will only set this flag on the head
    page; SLOB will not flag it at all.

10. BUDDY
    a free memory block managed by the buddy system allocator
    The buddy system organizes free memory in blocks of various orders.
    An order N block has 2^N physically contiguous pages, with the BUDDY flag
    set for and _only_ for the first page.

15. COMPOUND_HEAD
16. COMPOUND_TAIL
    A compound page with order N consists of 2^N physically contiguous pages.
    A compound page with order 2 takes the form of "HTTT", where H donates its
    head page and T donates its tail page(s).  The major consumers of compound
    pages are hugeTLB pages (Documentation/vm/hugetlbpage.txt), the SLUB etc.
    memory allocators and various device drivers. However in this interface,
    only huge/giga pages are made visible to end users.
17. HUGE
    this is an integral part of a HugeTLB page

19. HWPOISON
    hardware detected memory corruption on this page: don't touch the data!

20. NOPAGE
    no page frame exists at the requested address

21. KSM
    identical memory pages dynamically shared between one or more processes

    [IO related page flags]
 1. ERROR     IO error occurred
 3. UPTODATE  page has up-to-date data
              ie. for file backed page: (in-memory data revision >= on-disk one)
 4. DIRTY     page has been written to, hence contains new data
              ie. for file backed page: (in-memory data revision >  on-disk one)
 8. WRITEBACK page is being synced to disk

    [LRU related page flags]
 5. LRU         page is in one of the LRU lists
 6. ACTIVE      page is in the active LRU list
18. UNEVICTABLE page is in the unevictable (non-)LRU list
                It is somehow pinned and not a candidate for LRU page reclaims,
        eg. ramfs pages, shmctl(SHM_LOCK) and mlock() memory segments
 2. REFERENCED  page has been referenced since last LRU list enqueue/requeue
 9. RECLAIM     page will be reclaimed soon after its pageout IO completed
11. MMAP        a memory mapped page
12. ANON        a memory mapped page that is not part of a file
13. SWAPCACHE   page is mapped to swap space, ie. has an associated swap entry
14. SWAPBACKED  page is backed by swap/RAM
"""

LOCKED       =    1 << 0
ERROR        =    1 << 1
REFERENCED   =    1 << 2
UPTODATE     =    1 << 3
DIRTY        =    1 << 4
LRU          =    1 << 5
ACTIVE       =    1 << 6
SLAB         =    1 << 7
WRITEBACK    =    1 << 8
RECLAIM      =    1 << 9
BUDDY        =    1 << 10
MMAP         =    1 << 11
ANON         =    1 << 12
SWAPCACHE    =    1 << 13
SWAPBACKED   =    1 << 14
COMPOUND_HEAD=    1 << 15
COMPOUND_TAIL=    1 << 16
HUGE         =    1 << 17
UNEVICTABLE  =    1 << 18
HWPOISON     =    1 << 19
NOPAGE       =    1 << 20
KSM          =    1 << 21

UNKNOWN_32   =    1 << 32

#MASK_OF_INTERESTING_FLAGS = LOCKED | ERROR | REFERENCED | UPTODATE | DIRTY | LRU | ACTIVE | SLAB | WRITEBACK | RECLAIM | BUDDY | MMAP | SWAPCACHE | SWAPBACKED | HUGE | UNEVICTABLE | NOPAGE | KSM
MASK_OF_INTERESTING_FLAGS = LOCKED | ERROR | REFERENCED | UPTODATE | DIRTY | LRU | ACTIVE | SLAB | WRITEBACK | RECLAIM | BUDDY | MMAP | SWAPCACHE | SWAPBACKED | HUGE | UNEVICTABLE | NOPAGE | KSM

def set_interesting_pageflag_filter(flags_as_long):
    """ Only use the flags pased in the filter. E.g. all values read from the fil OR created as KPageFlags will be masked (and) with flags_as_long """ 
    global MASK_OF_INTERESTING_FLAGS
    MASK_OF_INTERESTING_FLAGS = flags_as_long

ALL_FLAGS = {
    LOCKED : 'LOCKED',
    ERROR : 'ERROR',
    REFERENCED : 'REFERENCED',
    UPTODATE : 'UPTODATE',
    DIRTY : 'DIRTY',
    LRU : 'LRU',
    ACTIVE : 'ACTIVE',
    SLAB : 'SLAB',
    WRITEBACK : 'WRITEBACK',
    RECLAIM : 'RECLAIM',
    BUDDY : 'BUDDY',
    MMAP : 'MMAP',
    ANON : 'ANON',
    SWAPCACHE : 'SWAPCACHE',
    SWAPBACKED : 'SWAPBACKED',
    COMPOUND_HEAD : 'COMPOUND_HEAD',
    COMPOUND_TAIL : 'COMPOUND_TAIL',
    HUGE : 'HUGE',
    UNEVICTABLE : 'UNEVICTABLE',
    HWPOISON : 'HWPOISON',
    NOPAGE : 'NOPAGE',
    KSM : 'KSM' ,
    UNKNOWN_32 : 'UNKNOWN_32'
    }

from datasource import DataSource
import struct


class FlagsDataSource(DataSource):
    _instances = {}

    def __init__(self, type, path ):
        DataSource.__init__(self, type, path, 'Q')

    def _parse_record(self, chunk):
        tmp =  struct.unpack(self.record_format, chunk)
        flags = tmp[0]
        interesting_flags = flags & MASK_OF_INTERESTING_FLAGS
        if FlagsDataSource._instances.has_key(interesting_flags):
            instance =  FlagsDataSource._instances[interesting_flags]
        else:
            instance =  KPageFlags(flags)
            FlagsDataSource._instances[interesting_flags] = instance

        return instance

class KPageFlags:

    def __hash__(self):
        return self.flags

    def __eq__(self,other):
        return None != other  and self.flags == other.flags

    def __ne__(self,other):
        return None == other  or self.flags != other.flags

    def __init__(self, flags, display = None):
        self.unfiltered = flags
        self.flags = (flags & MASK_OF_INTERESTING_FLAGS)
        if not display:
            display = "%0.16x : %s" % (flags, self.set_flags())

        self.display =  display

    def __repr__(self):
        return self.display

    def __getitem__(self, index):
        return self.flags & (1 << index)

    def all_set_in(self, flags):
        return (self.flags & flags) == flags

    def set_flags(self):
        all_set = filter(lambda (k,v): k & self.flags, ALL_FLAGS.iteritems())
        values = [ v for (k,v) in all_set ]
        return values
