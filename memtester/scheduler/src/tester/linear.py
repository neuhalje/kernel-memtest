'''
Created on Jun 1, 2010

@author: jens
'''

class LinearScanner(object):
    '''
    Scans a memory region (mmap) with linear complexity
    '''


    def __init__(self, reporting):
        '''
        Constructor
        reporting.report_bad_memory(bad_offset, expected_value, actual_value)
        '''
        self.reporting = reporting

    def name(self):
        return "Linear time test"

    def test(self, region, offset, len): 
        """
        - region supports __getitem(x)__ and __setitem(x,b)__, with b being casted to a byte 
        - offset is the first byte tested, len is the length (1..X). The bytes region[offset..offset+(length -1)] are tested
        
        return: last tested offset
        """
        
        last_element = offset+len
        # Test all ZEROes
        for index in xrange(offset, last_element):
            region[index] = 0
        
        for index in xrange(offset, last_element):
            v =  region[index]
            if not (v == 0):
                self.reporting.report_bad_memory(index, 0, v)

        # Test all ONEs
        for index in xrange(offset, last_element):
            region[index] = 0xff
       
        for index in xrange(offset, last_element):
            v =  region[index]
            if not (v == 0xff):
                self.reporting.report_bad_memory(index, 0xff, v)

        # Test all ADDRESS
        for index in xrange(offset, last_element):
            region[index] = index % 0xff
       
        for index in xrange(offset, last_element):
            v =  region[index]
            if not (v == (index % 0xff)):
                self.reporting.report_bad_memory(index, (index % 0xff), v)
                
        return last_element