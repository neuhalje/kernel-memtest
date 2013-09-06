#!/bin/env python
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

import unittest
import fcntl
from ctypes import *

import physmem 
import mmap 
import Helpers
from kpage  import *
from Helpers import find_free_buddy_pfns, find_anon_pfns
from physmem.physmem import SOURCE_FREE_BUDDY_PAGE, SOURCE_HW_POISON_ANON

class Test(unittest.TestCase):


    def setUp(self):
        self.device_name = "/dev/phys_mem"
        self.device = physmem.Physmem(self.device_name)
        self.IOCTL_CONFIGURE = 1074547456
        self.allowed_sources = physmem.SOURCE_HW_POISON_ANON

        self.assertEquals(8,sizeof(c_uint64),"unit64 != 8 bytes")
        x=POINTER(physmem.Phys_mem_frame_request)
        self.assertEquals(8,sizeof(x ),"pointer == %d bit, should be  64 bit" % (sizeof(x),))
        self.assertEquals(8,sizeof( POINTER(physmem.Phys_mem_frame_request)),"pointer == %d bit, should be  64 bit" % (sizeof( POINTER(physmem.Phys_mem_frame_request)),))
        self.assertEquals(16,sizeof(physmem.Phys_mem_frame_request),"Phys_mem_frame_request != 16 bytes")
        self.assertEquals(56,sizeof(physmem.Phys_mem_frame_status),"Phys_mem_frame_status != 56 bytes")
        self.assertEquals(24,sizeof(physmem.Phys_mem_request),"Phys_mem_request != 24 bytes")
        self.assertEquals(16,sizeof(physmem.Mark_page_poison),"Mark_page_poison != 16 bytes")
                
    def tearDown(self):
        pass

    def testOpenCloseDevice(self):
        with open(self.device_name, "rb") as f:
            pass

    def testOpenCloseDeviceMultipleTimes(self):
        with open(self.device_name, "rb") as f1:
            with open(self.device_name, "rb") as f2:
                pass

    def testOpenWriteableDevice(self):
        try:
            with open(self.device_name, "r+b") as f:
                self.fail("The device should not be writeable, when opened r/o")
        except IOError  as (errno, strerror):
            self.failUnlessEqual(1, errno, "Expected 'Operation not permitted'")


    def testIOCTL_no_elements(self):
        with open(self.device_name, "rb") as f:
            # IOCTL: 
            protocol_version = 1
            num_requests = 0
            preq = None
           
            arg = physmem.Phys_mem_request( protocol_version, num_requests, preq)
            rv = fcntl.ioctl(f,self.IOCTL_CONFIGURE, arg )

    def testIOCTL_invalid_elements(self):
        with open(self.device_name, "rb") as f:
            # IOCTL: 
            protocol_version = 1
            num_requests = 1     # One Element
            preq = None
            
            arg =  physmem.Phys_mem_request( protocol_version, num_requests, preq)
            try:
                rv = fcntl.ioctl(f,self.IOCTL_CONFIGURE, arg )
                self.fail("Passed a NULL-pointer as request, and told the device it was one element. Expected to fail, but did not!")
            except IOError  as (errno, strerror):
                self.failUnlessEqual(14, errno, "Expected 'Bad address', not %d (%s)" % (errno, strerror))

    def testIOCTL_invalid_version(self):
        with open(self.device_name, "rb") as f:
            # IOCTL: 
            protocol_version = 2
            num_requests = 0
            preq = None
            
            arg = physmem.Phys_mem_request( protocol_version, num_requests, preq)
            try:
                rv = fcntl.ioctl(f,self.IOCTL_CONFIGURE, arg )
                self.fail("Passed an invalid protocol version (%d) . Expected to fail, but did not!" % (protocol_version,))
            except IOError  as (errno, strerror):
                self.failUnlessEqual(22, errno, "Expected 'Invalid argument', not %d (%s)" % (errno, strerror))
         
         
    def test_Class_configure_no_elements(self):
            self.device.configure([])
#                             
       
       
    def test_Class_configure_one_element(self):
            requests = [physmem.Phys_mem_frame_request(10000,self.allowed_sources)]
            
            config = self.util_Class_configure(requests)
          
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
                print(answer)
                if (answer.is_claimed()):
                    print("Claimed!")
         
    def test_Class_configure_more_elements_no_source(self):
            allowed_sources = 0x0
            requests = []
            for pfn in xrange(0x40000, 0x40100):
                requests.append(physmem.Phys_mem_frame_request(pfn,allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
                #print(answer)
                if (answer.is_claimed()):
                    claimed += 1
                    
            print("Claimed: %d of %d" % (claimed, len(requests)))      
            self.assertEqual(0,claimed)
         
    def test_Class_configure_more_elements(self):
            requests = []
            for pfn in xrange(0x40000, 0x40100):
                requests.append(physmem.Phys_mem_frame_request(pfn,self.allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
                # print(answer)
                if (answer.is_claimed()):
                    claimed += 1
                    
            print("Claimed: %d of %d" % (claimed, len(requests)))      
            
       
    def test_Class_configure_more_free_buddies(self):
            pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "/proc/kpageflags")

            allowed_sources = self.allowed_sources
            
            requests = []
            free_buddies = find_free_buddy_pfns( pageflags, 0x100)
            for pfn in free_buddies:
                requests.append(physmem.Phys_mem_frame_request(pfn,allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
                # print(answer)
                if (answer.is_claimed()):
                    claimed += 1
                    
            print("Claimed: %d of %d" % (claimed, len(requests)))      

    def test_Class_configure_no_buddy_allocs_from_hwpoison(self):
            pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "/proc/kpageflags")

            allowed_sources = physmem.SOURCE_HW_POISON_ANON|physmem.SOURCE_HW_POISON_PAGE_CACHE
            
            requests = []
            free_buddies = find_free_buddy_pfns( pageflags, 0x100)
            for pfn in free_buddies:
                requests.append(physmem.Phys_mem_frame_request(pfn,allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
                # print(answer)
                if (answer.is_claimed()):
                    claimed += 1
                    
            self.assertEqual(0,claimed, "Claimed: %d of %d, although no buddy pages should be claimed by the hw-poison claimer" % (claimed, len(requests)))      
            
    def test_Class_configure_more_free_buddies_and_mmap(self):
            pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "/proc/kpageflags")

            requests = []
            free_buddies = find_free_buddy_pfns( pageflags, 0x100)
            for pfn in free_buddies:
                requests.append(physmem.Phys_mem_frame_request(pfn,self.allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
                # print(answer)
                if (answer.is_claimed()):
                    claimed += 1
                    
            print("Claimed: %d of %d" % (claimed, len(requests)))      
            with self.device.mmap(claimed * 4096) as map:
                pass
     
    def test_Class_configure_more_free_buddies_and_mmap_and_test(self):
        
            allowed_sources = SOURCE_FREE_BUDDY_PAGE
            pageflags = kpageflags.FlagsDataSource('flags', "/proc/kpageflags")
            
            pagecount = kpagecount.CountDataSource('count', "/proc/kpagecount")
            
            requests = []
            free_buddies = find_free_buddy_pfns( pageflags, 0x100)
            for pfn in free_buddies:
                requests.append(physmem.Phys_mem_frame_request(pfn,allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            with pageflags.open() as pf:
                with pagecount.open() as pc:
                    for request, answer in zip (requests,config):
                        # Test, if the request has been properly copied over to the configuration
                        self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                        self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                        
                        # print(answer)
                        if (answer.is_claimed()):
                            claimed += 1
                            pfn = answer.pfn

                            self.assertEqual(request.requested_pfn, answer.pfn, "requested and aquired pfn differ")

                            flags = pf[pfn]
                            count= pc[pfn]
                            
                            self.failIfEqual(None, flags,"Could not read flags for pfn %d" % (pfn,))
                            self.failIfEqual(None, count,"Could not read count for pfn %d" % (pfn,))
                            
                            self.assertFalse(flags.all_set_in(kpageflags.BUDDY),"The page should no longer be a free buddy page. The flags are %s" %(flags,)  )
                            #self.failIfEqual(0, flags.flags,"No  flags set for pfn %d" % (pfn,))

                            # We did not map the page yet, so expect 0 mapcount
                            # http://fixunix.com/kernel/488903-patch-2-5-pagemap-change-kpagecount-return-map-count-not-reference-count-page.html
                            self.assertTrue(count == 0 ,"Pagecount should be 0, but is %d" % (count,))
                            
                    print("Claimed: %d of %d" % (claimed, len(requests)))
                    
                    size = claimed * 4096
                    with self.device.mmap(size) as map:
                        self.failIfEqual(None, map, "No map returned")
                        self.assertEquals(0,map.tell(),"Pointer into mapping should start at 0")

                        # test mapcont
                        for  answer in  config:
                            if (answer.is_claimed()):
                                pfn = answer.pfn
                                
                                flags = pf[pfn]
                                count= pc[pfn]
    
                                self.failIfEqual(None, flags,"Could not read flags for pfn %d" % (pfn,))
                                self.failIfEqual(None, count,"Could not read count for pfn %d" % (pfn,))
    
                                # We did  map the page yet, so expect 1 mapcount
                                # http://fixunix.com/kernel/488903-patch-2-5-pagemap-change-kpagecount-return-map-count-not-reference-count-page.html
                                self.assertTrue(count == 1 ,"Pagecount should be 1 becuase we did map the page, but is %d" % (count,))

                        for i in xrange(0,size):
                            map.write_byte(chr(i % 0xff))
                            
                        self.assertEqual(size, map.tell(),"Did not reach end of file")
                        map.seek(0)    
                        self.assertEquals(0,map.tell(),"After seek(0): Pointer into mapping should be at 0")
        
                        for i in xrange(0,size):
                            expected = i % 0xff
                            found = ord( map.read_byte())
                            self.assertEqual(expected, found,"Expected value %x at %d, not %x" % (expected,i,found))
                            
    def test_no_source(self):
        """ This test is expected to fail """
        if False or True:
            first_pfn = 0x100000
            count = 0x10000
            pfns = xrange(first_pfn, first_pfn+count)
            self.configure_mmap_and_test(pfns, 0)

    def test_hwpoison_anon(self):
        pageflags = kpageflags.FlagsDataSource('flags', "/proc/kpageflags")

        pfns = find_anon_pfns(pageflags, 0x1000)
        # Skip the first 'few' pages
        pfns = pfns[-5:]
        self.configure_mmap_and_test(pfns, SOURCE_HW_POISON_ANON)

    def test_buddies(self):
        pageflags = kpageflags.FlagsDataSource('flags', "/proc/kpageflags")

        pfns = find_free_buddy_pfns(pageflags, 0x1000)
        self.configure_mmap_and_test(pfns, SOURCE_FREE_BUDDY_PAGE)

    def test_pageflags_num_frames(self):
            pageflags = kpageflags.FlagsDataSource('flags', "/proc/kpageflags")
            with pageflags.open() as pf:
                frames = pf.num_frames()
                min_expected = 0x10000
                self.assertTrue(frames > min_expected, "I would expect more than 0x%x frames, but only found 0x%x." % (min_expected, frames))
                
    def configure_mmap_and_test(self, pfns, allowed_sources = None ):
            """  Claim and test the pageframes named by the list of PFNs by using the allowed_sources.
                  The tests include mapping and a basic memory test
            """
            
            if None == allowed_sources: allowed_sources = self.allowed_sources
            
            pageflags = kpageflags.FlagsDataSource('flags', "/proc/kpageflags")
            
            pagecount = kpagecount.CountDataSource('count', "/proc/kpagecount")
            
            requests = []
            for pfn in pfns:
                requests.append(physmem.Phys_mem_frame_request(pfn,allowed_sources))
            
            config = self.util_Class_configure(requests)
             
            claimed = 0
            
            with pageflags.open() as pf:
                with pagecount.open() as pc:
                    for request, answer in zip (requests,config):
                        # Test, if the request has been properly copied over to the configuration
                        self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                        self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                        
                        # print(answer)
                        if (answer.is_claimed()):
                            claimed += 1
                            pfn = answer.pfn

                            self.assertEqual(request.requested_pfn, answer.pfn, "requested and aquired pfn differ")

                            flags = pf[pfn]
                            count= pc[pfn]
                            
                            self.failIfEqual(None, flags,"Could not read flags for pfn %d" % (pfn,))
                            self.failIfEqual(None, count,"Could not read count for pfn %d" % (pfn,))
                            
                            # self.assertFalse(flags.all_set_in(kpageflags.BUDDY),"The page should no longer be a free buddy page. The flags are %s" %(flags,)  )
                            #self.failIfEqual(0, flags.flags,"No  flags set for pfn %d" % (pfn,))

                            # We did not map the page yet, so expect 0 mapcount
                            # http://fixunix.com/kernel/488903-patch-2-5-pagemap-change-kpagecount-return-map-count-not-reference-count-page.html
                            self.assertTrue(count == 0 ,"Pagecount should be 0, but is %d" % (count,))
                            
                    print("Claimed: %d of %d" % (claimed, len(requests)))
                    
                    self.assertTrue( claimed > 0, "No pages claimed using method(s) 0x%x " % (allowed_sources,))
                    
                    size = claimed * 4096
                    with self.device.mmap(size) as map:
                        self.failIfEqual(None, map, "No map returned")
                        self.assertEquals(0,map.tell(),"Pointer into mapping should start at 0")

                        # test mapcont
                        for  answer in  config:
                            if (answer.is_claimed()):
                                pfn = answer.pfn
                                
                                flags = pf[pfn]
                                count= pc[pfn]
    
                                self.failIfEqual(None, flags,"Could not read flags for pfn %d" % (pfn,))
                                self.failIfEqual(None, count,"Could not read count for pfn %d" % (pfn,))
    
                                # We did  map the page yet, so expect 1 mapcount
                                # http://fixunix.com/kernel/488903-patch-2-5-pagemap-change-kpagecount-return-map-count-not-reference-count-page.html
                                self.assertTrue(count == 1 ,"Pagecount should be 1 becuase we did map the page, but is %d" % (count,))

                        for i in xrange(0,size):
                            map.write_byte(chr(i % 0xff))
                            
                        self.assertEqual(size, map.tell(),"Did not reach end of file")
                        map.seek(0)    
                        self.assertEquals(0,map.tell(),"After seek(0): Pointer into mapping should be at 0")
        
                        for i in xrange(0,size):
                            expected = i % 0xff
                            found = ord( map.read_byte())
                            self.assertEqual(expected, found,"Expected value %x at %d, not %x" % (expected,i,found))
    
                            
                      
    def util_Class_configure(self, requests):
            self.device.configure(requests)
            config = self.device.read_configuration()
            self.assertEquals(len(requests), len(config) )
            
            # I expect them to be  in the same order
            for request, answer in zip (requests,config):
                # Test, if the request has been properly copied over to the configuration
                self.assertEqual(request.requested_pfn, answer.request.requested_pfn, "request.requested_pfn differs from the request read from the device")
                self.assertEqual(request.allowed_sources, answer.request.allowed_sources, "request.allowed_sources differs from the request read from the device")
                
            return config

    def testIOCTL_no_element_but_data(self):
        with open(self.device_name, "rb") as f:
            # IOCTL: 
            protocol_version = 1
            num_requests = 0
            
            pfn_request =  physmem.Phys_mem_frame_request(1,1)
            preq = pointer(pfn_request)
            
            arg = physmem.Phys_mem_request( protocol_version, num_requests, preq)
            rv = fcntl.ioctl(f,self.IOCTL_CONFIGURE, arg )
#  
#    def testIOCTL_one_element(self):
#        with open(self.device_name, "rb") as f:
#            # IOCTL: 
#            protocol_version = 1
#            num_requests = 1
#            
#            pfn_request =  physmem.Phys_mem_frame_request(1,1)
#            preq = pointer(pfn_request)
#            
#            arg = physmem.Phys_mem_request( protocol_version, num_requests, preq)
#            rv = fcntl.ioctl(f,self.IOCTL_CONFIGURE, arg )
#              
#               

if __name__ == "__main__":
    import sys
    # sys.argv = ['', 'Test.test_buddies', 'Test.test_hwpoison_anon']
    #sys.argv = ['', 'Test.test_hwpoison_anon']
    #sys.argv = ['', 'Test.test_no_source']
    #sys.argv = ['', 'Test.test_buddies']
    sys.argv = ['', 'Test.test_pageflags_num_frames']
    unittest.main()
