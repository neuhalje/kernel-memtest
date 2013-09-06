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
from  kpage import *


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testImport(self):
        kpageflags.FlagsDataSource(kpageflags.KPageFlags, "/dev/zero")

    def testOpen(self):
        pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "/dev/zero")
        with pageflags.open() as pf:
            pass


    def testReadSequential(self):
        pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "./kpageflags.bin")
        count = 0
        with pageflags.open() as pf:
            while True:
                    flags = pf.next_record()
                    if  (None == flags):
                        break
                    count += 1
                    
        recordcount = pageflags.get_record_count()
        
        self.assertEquals(recordcount, count, "Mismatch between  get_record_count (%d) and number of items read (%d)" % (recordcount, count))
                    
    def testReadByIndex(self):
        pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "./kpageflags.bin")
        count = 0
        cache = {}
        
        recordcount = pageflags.get_record_count()
        if (recordcount == 0 ):
            """ /proc/kpageflags does not work for get_record_count"""
            recordcount = 100
            
        # Read the first n flags into the cache
        with pageflags.open() as pf:
            while count < recordcount:
                    flags = pf[count]
                    self.assertFalse  (None == flags)
                    cache[count] = flags
                    count += 1

        # re-open the file and verify the flags
        # This only works, if the file the datasource points to
        # is constant ...
        with pageflags.open() as pf:
            while count > 0:
                    count -= 1
                    flags = pf[count]
                    self.assertFalse  (None == flags)
                    
                    self.assertEquals( cache[count] , flags,"Mismatch")
                    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testImport']
    unittest.main()