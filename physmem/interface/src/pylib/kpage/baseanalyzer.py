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
import time



class BaseAnalyzer:
    """ 
     Analyzes a binary file made of records. Subclasses implement event
     handlers that are called for each step in the processing workflow.
    """
    def analyze(self, pageflags, pagecount):
        """
         Opens the file passed in by `pageflags`/`pagecount` (type DataSource) 
         and iterates over each record in the files.
        """


        self.start_processing()
        index =  0

        with pageflags.open() as pf:
            with pagecount.open() as pc:
                while True:
            
                    pf = pageflags.next_record()
                    pc = pagecount.next_record()
 
                    if  (None == pf  or None ==  pc):
                        break
              
                    self.process_record(index, pc, pf)
                    index += 1

        self.stop_processing()

    def process_record(self, pfn, page_count, page_flags):
        pass

    def start_processing(self):
        pass

    def stop_processing(self):
        pass
