#!/usr/bin/env python
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

import os
import glob

from baseanalyzer import BaseAnalyzer
from datasource import ConstantDataSource
from kpageflags import *
from optparse import OptionParser


class FlagsAggregator(BaseAnalyzer):
    """
    This class can be used to build stastistics from collected `kpageflags`/`kpagecount`.
    """

    def __init__(self, print_status_for_each_fileset, reset_statistics_after_each_fileset):
        self.pf_statistics = {}
        self.print_status_for_each_fileset = print_status_for_each_fileset
        self.reset_statistics_after_each_fileset = reset_statistics_after_each_fileset
        
    def process_record(self, pfn, page_count, page_flags):

        if self.pf_statistics.has_key(page_flags):
            self.pf_statistics[page_flags] = self.pf_statistics[page_flags] + 1
        else:
            self.pf_statistics[page_flags] = 1

    def stop_processing(self):
        if self.print_status_for_each_fileset:
            self.print_status()
    
    def print_status(self):
        print("Found %d different flags." % len(self.pf_statistics))
        flags = [ (k, v) for k, v in self.pf_statistics.iteritems() ]
        flags = sorted(flags, key=lambda x: x[1], reverse=True) 
        for top in flags[:10]:
            print("%0.16s \t %d" % (top[0],  top[1]))
            print("\t%s " % (top[0].set_flags(),  ))

    def start_processing(self):
        if self.reset_statistics_after_each_fileset:
            self.pf_statistics =  {}

if __name__ == "__main__":
    # 
    usage = """This tool builds statistics from collected `kpageflags`.
    usage: %prog [options] sourcedir"""
    parser = OptionParser(usage=usage)


    parser.add_option("-v", action="store_true", dest="verbose",
                  help="Print filenames as they are processed.", default=False)

    parser.add_option("-p", "--pattern",
                      default='*kpageflags*.bin',
                      metavar="PATTERN", help="use this PATTERN (glob) to filter the page-flags files. [default: %default]")
    parser.add_option("-m", "--mode",
                      default="grouped",choices=["grouped","single"],
                      help="Aggregationmode: grouped (for all files) or single (statistics for each file)"
                           "[default: %default]")
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    is_per_file = ("single" == options.mode)

    pagecount = ConstantDataSource('count','1')

    analyzer = FlagsAggregator(is_per_file,is_per_file)

    path = args[0]

    for infile in  glob.glob( os.path.join(path, options.pattern) ):
        if options.verbose:
            print(infile)
        pageflags = FlagsDataSource('flags',infile)
        analyzer.analyze(pageflags, pagecount)

    analyzer.print_status()
