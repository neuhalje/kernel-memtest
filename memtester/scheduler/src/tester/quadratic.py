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

class QuadraticScanner(object):
    '''
    Scans a memory region (mmap) with n**2  complexity
    '''


    def __init__(self, reporting):
        '''
        Constructor
        reporting.report_bad_memory(bad_offset, expected_value, actual_value)
        '''
        self.reporting = reporting


    def name(self):
        return "Quadratic runtime test"
    
    def test(self, region, offset, len): 
        """
        - region supports __getitem(x)__ and __setitem(x,b)__, with b being casted to a byte 
        - offset is the first byte tested, len is the length (1..X). The bytes region[offset..offset+(length -1)] are tested
        
        return: last tested offset
        """
        
        last_element = offset+len
        
        # Test all ZEROes - first reset
        for index in xrange(offset, last_element):
            region[index] = 0
        
        for index in xrange(offset, last_element):
            v =  region[index]
            if not (v == 0):
                self.reporting.report_bad_memory(index, 0, v)

        # Test all ONEs -- quadratic runtime (linear number of writes, quadratic number of reads)
        for index in xrange(offset, last_element):
            region[index] = 0xff
            
            for before in xrange(offset, index + 1):
                v =  region[before]
                if not (v == 0xff):
                    self.reporting.report_bad_memory(before, 0xff, v)
            
            for after in xrange( index + 1, last_element):
                v =  region[after]
                if not (v == 0x00):
                    self.reporting.report_bad_memory(after, 0x00, v)
                
         
        # Test all ZEROes - second reset
        for index in xrange(offset, last_element):
            region[index] = 0
        
        for index in xrange(offset, last_element):
            v =  region[index]
            if not (v == 0):
                self.reporting.report_bad_memory(index, 0, v)
   
        return last_element
