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

import frame
import physmem


def get_frame_config_class():
        return frame.FrameStatus

class SimpleBlockwiseSchedulerFactory():
    def __init__(self, physmem_device,frame_test,  kpageflags, kpagecount, timestamping, reporting):
        '''
        Constructor
        '''
        self.kpageflags = kpageflags
        self.kpagecount = kpagecount
        self.physmem_device = physmem_device
        self.frame_test = frame_test
        self.timestamping = timestamping
        self.max_untested_age = self.timestamping.seconds_to_timestamp( 60*60*24  )
        self.max_untested_age = 0
        self.reporting =  reporting

    def new_instance(self, frame_stati):
       return SimpleBlockwiseScheduler( self.physmem_device, self.frame_test, frame_stati, self.kpageflags, self.kpagecount, self.timestamping, self.reporting)

    def name(self):
        return "Blockwise Allocation Scheduler"
    
class SimpleBlockwiseScheduler(object):
    '''
    This scheduler iterates over all frames in the status and tests the frame, based on the evaluation function
    '''

    def __init__(self, physmem_device,frame_test, frame_stati, kpageflags, kpagecount, timestamping, reporting):
        '''
        Constructor
        '''
        self.frame_stati = frame_stati
        self.kpageflags = kpageflags
        self.kpagecount = kpagecount
        self.physmem_device = physmem_device
        self.frame_test = frame_test
        self.timestamping = timestamping 
        self.max_untested_age = self.timestamping.seconds_to_timestamp( 60*60*24  )
        self.max_untested_age = 0
        self.reporting =  reporting

    def name(self):
        return "Blockwise Allocation Scheduler"
        
    def run(self, first_frame,last_frame, allowed_sources):
        
        max_blocksize = 100
        max_non_matching = 100
        
        cur_non_matching = 0
        
        block = []
        
        for pfn in xrange(first_frame, last_frame):
            frame_status = self._pfn_status(pfn)
            
            if ( self.should_test(frame_status)):
                block.append(frame_status)
                cur_non_matching = 0
            else:
                cur_non_matching += 1
                
            if (len(block) == max_blocksize ) or (cur_non_matching >= max_non_matching): 
                if (len(block) > 0 ):   
                    self.test_frames_and_record_result(block, allowed_sources)
                    block = []
                cur_non_matching = 0

        if (len(block) > 0  ):
                self.test_frames_and_record_result(block, allowed_sources)
                
                
            
    def  should_test(self,frame_status):
        now = self.timestamping.timestamp()
        time_untested = now - frame_status.last_successfull_test
        
        return  (time_untested > self.max_untested_age )

    def  test_frames_and_record_result(self,frame_stati, allowed_sources):
        
        pfns = [frame_status.pfn for  frame_status in frame_stati]
        
        status_by_pfn = dict([ (frame_status.pfn, frame_status) for  frame_status in frame_stati])

        results = self._claim_pfns(pfns, allowed_sources)

        num_frames_claimed = 0
        
        for frame in results:
            if  frame.pfn in status_by_pfn:
                if frame.is_claimed():    
                    num_frames_claimed += 1
                    
        for frame in results:
            if  frame.pfn in status_by_pfn:
                frame_status = status_by_pfn[frame.pfn]
                frame_status.last_claiming_attempt =  self.timestamping.timestamp()
                    
                if frame.is_claimed():
                    frame_status.last_claiming_time_jiffies = frame.allocation_cost_jiffies
                    frame_status.last_successfull_claiming_method = frame.actual_source
                    
                    is_ok = False
                    
                    with self.physmem_device.mmap(physmem.PAGE_SIZE * num_frames_claimed) as map:
                        # It is better to handle bad frames after they are unmapped
                        is_ok = self.frame_test.test(map,frame.vma_offset_of_first_byte  ,physmem.PAGE_SIZE)
        
                    if is_ok:
                        frame_status.has_errors = 0
                        frame_status.last_successfull_test = self.timestamping.timestamp() 
                        self._report_good_frame(frame.pfn)         
                    else:
                        frame_status.num_errors += 1
                        self.physmem_device.mark_pfn_bad(frame.pfn)
                        self._report_bad_frame(frame.pfn)         
                               
            else:
                # Hmm, better luck next time
                self._report_not_aquired_frame(frame_status.pfn)

    def _report_not_aquired_frame(self, pfn):
        pass
            
    def _report_good_frame(self, pfn):
        self.reporting.report_good_frame(pfn)

    def _report_bad_frame(self, pfn):
        self.reporting.report_bad_frame(pfn)
    
    def _claim_pfns(self, pfns,allowed_sources):
        requests = []
        for pfn in pfns:
            requests.append(physmem.Phys_mem_frame_request(pfn, allowed_sources))
         
        self.physmem_device.configure(requests)
        config = self.physmem_device.read_configuration()
        
        if not ( len(requests) ==  len(config) ) :
            # Error
            raise RuntimeError("The result read from the physmem-device contains %d elements, but I expected %d elements! " %  (len(config),len(requests)))
        
        return config
            
    def _pfn_status(self, pfn):
        flags = self.kpageflags[pfn]
        mapcount = self.kpagecount[pfn]
        
        status = self.frame_stati[pfn]
        
        status.pfn = pfn
        status.flags =flags
        status.mapcount = mapcount
        
        return status
    

