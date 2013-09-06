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

import struct
from ctypes import *
import fcntl

import mmap

import mmapwrapper

PAGE_SIZE = 0x1000

SOURCE_FREE_PAGE                =  0x00001          # /* Use the 'Free Pages' Claimer (currently disabled) */
SOURCE_FREE_BUDDY_PAGE  =  0x00002  #     /* Use the 'Free Buddy' Claimer: Use a free page associated with the buddy system */

SOURCE_PAGE_CACHE             =  0x00004        # /* Use the  'wrest a page from the page cache'-claimer */
SOURCE_ANONYMOUS            =  0x00008       # /* Use the  'steal the page from a user process' claimer  */

SOURCE_ANY_PAGE                  =  0x00010           #  /* Let the module decide */

SOURCE_HW_POISON_ANON   =  0x00020   #       /* Use the HW_POISON claimer */
SOURCE_HW_POISON_PAGE_CACHE    =  0x00040  #     /* Use the HW_POISON claimer */
SOURCE_HW_POISON               =       (SOURCE_HW_POISON_ANON |  SOURCE_HW_POISON_PAGE_CACHE)

class Mark_page_poison(Structure):

    # struct mark_page_poison{
    #  unsigned  long protocol_version; /* The protocol/struct version of this IOCTL call. Must be IOCTL_REQUEST_VERSION */
    #  unsigned  long bad_pfn;     /* The bad pfn */
    # };
    _fields_ = [("protocol_version", c_uint64),
                      ("bad_pfn", c_uint64)]
    
    
class Phys_mem_frame_request(Structure):
    #/**
    # * A single request for a single pfn
    # */
    #struct phys_mem_frame_request {
    #   unsigned long requested_pfn;
    #   unsigned long allowed_sources; /* Bitmask of SOURCE_* */
    #};
    _fields_ = [("requested_pfn", c_uint64),
                      ("allowed_sources", c_uint64)]
    
    def __str__(self):
        return "pfn:%d, allowed_sources:%x" % (self.requested_pfn, self.allowed_sources)

class Phys_mem_request(Structure):
    # struct phys_mem_request {
    #  unsigned long protocol_version; /* The protocol/struct version of this IOCTL call. Must be IOCTL_REQUEST_VERSION */
    # unsigned long num_requests;     /* The number of frame requests */
    # struct phys_mem_frame_request __user  *req; /* A pointer to the array of requests. The array must contain at least num_requests items */
    # };
    _fields_ = [("protocol_version", c_uint64),
                ("num_requests", c_uint64),
                ("preq", POINTER(Phys_mem_frame_request))]


class Phys_mem_frame_status(Structure):

    #struct  {
    #   struct phys_mem_frame_request        request;
    #   unsigned long                        vma_offset_of_first_byte;      /* A pointer to the first byte of the frame, relative to the start of the VMA */
    #   unsigned long                               pfn;                    /* The pfn of the frame */
    #   u64                                  allocation_cost_jiffies;       /* How long did it take to get a hold on this frame? Measured in jiffies*/
    #   unsigned long                        actual_source;                 /* A single item of SOURCE_* (optionally ORed with one SOURCE_ERROR_**/
    #   struct page*                         page;                          /* The claimed (get_page) page describing this pfn OR NULL, when the page could not be claimed */
    #};
    _fields_ = [("request", Phys_mem_frame_request),
                ("vma_offset_of_first_byte", c_uint64),
                ("pfn", c_uint64),
                ("allocation_cost_jiffies", c_uint64),
                ("actual_source", c_uint64),
                ("page_p", c_uint64)]
    
    def __str__(self):
       return "pfn %xd: %s, actual_source: %x vma_offset_of_first_byte:%d, page_p:%x" % (self.pfn, self.request, self.actual_source, self.vma_offset_of_first_byte, self.page_p)
   
    def is_claimed(self):
        return self.page_p != 0
        
class Physmem:
    def __init__(self, device):
        self.device_name = device
        self.IOCTL_CONFIGURE = 0x40184b00
        self.IOCTL_MARK_PFN_BAD = 0x40104b01
        self.f = None

    def __del__(self):
        if self.f and not self.f.closed:
            self.f.close
        
        self.f = None
                
    def dev(self):
        if not self.f or self.f.closed:
            self.f = open(self.device_name, "rb+")
        
        return self.f

    def mark_pfn_bad(self, bad_pfn):
            protocol_version = 1
            request = Mark_page_poison(protocol_version,bad_pfn)
            #preq =   cast(request, POINTER(Mark_page_poison))

            rv = fcntl.ioctl(self.dev(),self.IOCTL_MARK_PFN_BAD, request )
            return rv
        
    def configure(self, requested_pfns):
            """
            Expects a list of Phys_mem_frame_request instances
            """
                # IOCTL: 
            protocol_version = 1
            
            if    (not requested_pfns) \
               or (len(requested_pfns) == 0):
                
                num_requests = 0
                preq = None
            else:
                # FIXME! : Array bauen
                num_requests = len(requested_pfns)
                
                RequestArray = Phys_mem_frame_request * num_requests
                
                requests = RequestArray(*requested_pfns)
                preq =   cast(requests, POINTER(Phys_mem_frame_request))

            
            arg = Phys_mem_request( protocol_version, num_requests, preq)
            rv = fcntl.ioctl(self.dev(),self.IOCTL_CONFIGURE, arg )
            return rv
        
    def read_configuration(self):
        """
        Read and return the configuration from the device. 
        Returns a list of  Phys_mem_frame_status
        """
        ret = []
#        from_buffer_copy
        objsize = sizeof(Phys_mem_frame_status)
        f = self.dev()
        offset = 0
        f.seek(offset)
   
        eof = False
        
        while not eof:
            chunk = f.read(objsize)
            if chunk:
                obj = Phys_mem_frame_status.from_buffer_copy(chunk)
                ret.append(obj)
            else:
                eof = True
        return ret

    def mmap(self, length):
        fileno = self.dev().fileno()
        #map = mmap.mmap(fileno,4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        map = mmap.mmap(fileno, length, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        wrapped = mmapwrapper.MmapWrapper(map)
        
        return wrapped