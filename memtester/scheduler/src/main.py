#!/usr/bin/python
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


try:
    import kpage
    import physmem
except ImportError as e:
    print "Do not forget to include '{TOP_LEVEL}/physmem/interface/src/pylib/' into PYTHONPATH"
    raise e

import status
import scheduling
import scheduling.simple.frame
import sys
import tester

import time
from optparse import OptionParser


class PrintTestReporting:
    def report_bad_memory(self, bad_offset, expected_value, actual_value):
        print("BAD memory, offset 0x%x : Expected/Got 0x%x/0x%x" % (bad_offset, expected_value, actual_value))
        


class PrintSchedulerReporting:
    def __init__(self, chunksize ):
        self.chunksize = chunksize
        self.enabled = (chunksize != 0)
        self.reset()
        
    
    def reset(self):
        self.frames_tested  = 0
        self.frames_tested_c  = 0
        self.start_of_measurement = time.time()
        self.start_of_chunk = self.start_of_measurement
        
    def report_good_frame(self, pfn):
        self.report_frame_tested()
    
    def report_bad_frame(self, pfn):
        self.report_frame_tested()

    def report_frame_tested(self):
        self.frames_tested += 1
        self.frames_tested_c += 1
        if self.enabled:
            if (self.frames_tested % self.chunksize) == 0:
                self.print_stats()

    def print_stats(self):
        seconds_since_start = time.time() - self.start_of_measurement
        seconds_since_start_c = time.time() - self.start_of_chunk
        if (seconds_since_start_c > 0):
            fps = self.frames_tested / seconds_since_start
            fps_c = self.frames_tested_c / seconds_since_start_c
            print("\tTested %d frames in %d seconds. fps=%d (this batch: %d in %d s: fps=%d)" % (self.frames_tested,seconds_since_start, fps, self.frames_tested_c, seconds_since_start_c,fps_c))
            self.frames_tested_c = 0
            self.start_of_chunk = time.time()
    
def print_stats(config,timestamping):
    #("last_successfull_test", c_uint64), ("last_failed_test", c_uint64), ("last_claiming_time_jiffies", c_uint64), 
    #                  ("last_claiming_attempt", c_uint64),
    #                 ("num_errors", c_uint32),
    #                  ("last_successfull_claiming_method", c_uint32)]
    
    num_tested = 0
    num_untested = 0
    
    total_claim_time  = 0
    min_claim_time = None
    max_claim_time = 0
   
    total_last_test_timestamp = 0
    min_last_test_timestamp = None
    max_last_test_timestamp = 0
    
    num_errors = 0
    num_frames = config.get_record_count()
    
    for pfn in xrange(0, num_frames):
        frame = config[pfn]
        
        is_tested = (frame.last_successfull_test > 0)
        
        if is_tested:
            num_tested += 1
            if (frame.last_successfull_test < min_last_test_timestamp or not min_last_test_timestamp) and (frame.last_successfull_test >0) :
                min_last_test_timestamp = frame.last_successfull_test 
                
            if (frame.last_successfull_test > max_last_test_timestamp) or (0 == max_last_test_timestamp):
                max_last_test_timestamp = frame.last_successfull_test 
                
            if (frame.last_failed_test < min_last_test_timestamp or not min_last_test_timestamp) and (frame.last_failed_test >0) :
                min_last_test_timestamp = frame.last_failed_test 
                
            if (frame.last_failed_test > max_last_test_timestamp) or (0 == max_last_test_timestamp):
                max_last_test_timestamp = frame.last_failed_test 
                          
            total_last_test_timestamp += frame.last_successfull_test
            
            if (frame.last_claiming_time_jiffies < min_claim_time) or (None == min_claim_time):
                min_claim_time = frame.last_claiming_time_jiffies 
                
            if (frame.last_claiming_time_jiffies > max_claim_time) or (0 == max_claim_time):
                max_claim_time = frame.last_claiming_time_jiffies
                
            total_claim_time +=  frame.last_claiming_time_jiffies

            if (frame.num_errors > 0 ):
                num_errors += 1
                
        else:
            num_untested += 1
   
    print("0x%x frames (%d decimal), of which are %d tested  (%02.1f %%) and %d untested  (%02.1f %%), %d have seen errors." % (num_frames,num_frames, num_tested, (100.0 * num_tested/num_frames) , num_untested, (100.0 * num_untested/num_frames) , num_errors))
    if num_tested > 0:
        print("For tested frames, the following statistics have been calculated: ")
        print("\tTime it took to claim a frame (in jiffies) (min,max,avg) : %d, %d, %d" % (min_claim_time, max_claim_time, total_claim_time / num_tested))   
        print("\tTimestamp of last test (min,max,avg) : %s, %s, %s" % (timestamping.to_string( min_last_test_timestamp, '-'), timestamping.to_string(max_last_test_timestamp), timestamping.to_string(total_last_test_timestamp / num_tested)))   

def reset_first_10_frames_in_config(path):
    """
    Reset the first 10 frames of the config
    """
    num_frames = 10
    cfg = status.FileBasedConfiguration(path, num_frames,  scheduling.simple.frame.FrameStatus)
    with cfg.open() as s:
        for idx in xrange(0,num_frames):
            stat = s[idx]
            stat.last_successfull_test = 0
            stat.last_failed_test = idx
            
    with cfg.open() as s:
        for idx in xrange(0,num_frames):
            stat = s[idx]
            if  (stat.last_successfull_test != 0) or ( stat.last_failed_test != idx):
                print("Error @%d: got %s" % (idx,stat))
            
if __name__ == '__main__':


    usage = """This tool tests your computers memory. Be sure that the phys_mem module is loaded! Alos, access to  `/proc/kpageflags`/`/proc/kpagecount` is needed
    usage: %prog [options]"""
    parser = OptionParser(usage=usage)


    parser.add_option("-a", "--allocation-strategy",dest="strategy",type="choice",
                      default="blockwise",choices=["blockwise","frame-by-frame"],
                      help="Algorithm used to allocate memory: `blockwise` and `frame-by-frame`."
                           "[default: %default]")

    parser.add_option("-t", "--test-algorithm",dest="algorithm",type="choice",
                      default="linear",choices=["linear","quadratic"],
                      help="Algorithm used to verify frames: `linear`-time or `quadratic` runtime."
                           "[default: %default]")

    parser.add_option("-f", "--report-frequency",dest="report_every",
                      default=50,type=int ,
                      help="Report performance statistics every REPORT_EVERY frames. `0` disables this report."
                           "[default: %default]")

    parser.add_option("-s", "--status_file",dest="status_file",
                      default='/tmp/memtest_status',
                      metavar="PATH", help="The path to the status file used by this program. The file will be created, if it does not exists. [default: %default]")

    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("No arguments supported!")

    if options.report_every < 0:
        parser.error("report-frequency must be > 0")

    path = options.status_file
 
    timestamping = status.TimestampingFacility()
    
    pageflags = kpage.FlagsDataSource('flags', "/proc/kpageflags").open()
    pagecount = kpage.CountDataSource('count', "/proc/kpagecount").open()

    num_frames = pageflags.num_frames()


    if  "frame-by-frame" == options.strategy:
        frame_config_class = scheduling.simple.get_frame_config_class()
    elif "blockwise" == options.strategy:
        frame_config_class = scheduling.blockwise.get_frame_config_class()

    cfg = status.FileBasedConfiguration(path, num_frames, frame_config_class)
                
    device_name = "/dev/phys_mem"
    physmem_dev  = physmem.Physmem(device_name)
    
    allowed_sources = physmem.SOURCE_FREE_BUDDY_PAGE


    if  "linear" == options.algorithm:
        test = tester.LinearScanner(PrintTestReporting())
    elif "quadratic" == options.algorithm:
        test = tester.QuadraticScanner(PrintTestReporting())


    reporting = PrintSchedulerReporting(options.report_every)
    
    if  "frame-by-frame" == options.strategy:
        scheduler_factory = scheduling.simple.SimpleSchedulerFactory(physmem_dev, test,  pageflags, pagecount, reporting)
    elif "blockwise" == options.strategy:
        scheduler_factory =  scheduling.blockwise.SimpleBlockwiseSchedulerFactory(physmem_dev, test, pageflags, pagecount, timestamping, reporting)

    print "Using the '%s' with a '%s' test algorithm" % (scheduler_factory.name(), test.name())

    while True:
        with cfg.open() as s:
            print_stats(s,timestamping) 
                
        with cfg.open() as s:
            reporting.reset()

            scheduler = scheduler_factory.new_instance(s)
            scheduler.run(0,num_frames, allowed_sources)
            
            reporting.print_stats()
        
    with cfg.open() as s:
        print_stats(s,timestamping) 

