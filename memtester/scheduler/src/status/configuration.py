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

import mmap
import kpage
import struct

from ctypes import *
import sys


def _open_create( path, len):
    """ Open the file and make it the length passed. If the file does not exist, create it and fill it with 0"""
    f = None
    try:
        f = open(path, 'r+b')
    except:
        pass

    if not f:
        f = open(path, 'w+b')
     
    f.seek(len)
    f.truncate()
    f.seek(0)
    return f


class FileBasedConfiguration():
    '''
    Implements a memory-map- based configuration..
    - Each frame is represented by an instance of FrameStatus
    - The frames can be read by using the __getitem__ interface, indexing it by PFN
    - The fields inside the returned FrameStatus-instance directly map to the file, i.e.
       CHANGING THE INSTANCE CHANGES THE FILE
       
       E.g.: To update pfn 4711
       
       inst1 = cfg[4711]
       inst2 = cfg[4711]
       inst1.status = 12345
       print(inst2.status) # --> 12345
       inst2.status = 6789
       print(inst1.status) # --> 6789
       
       
    '''

    def __init__(self,  path, num_frames, instance_clazz):
        self.instance_clazz = instance_clazz
        self.num_frames = num_frames
        self.record_size = sizeof(instance_clazz)
        self.path = path
        self.file = None
        self.map = None


    def get_record_count(self):
        """
        Return the number of records in the file
        """
        return  self.num_frames

  
    def open(self):
        self.close()
        size = self.num_frames * self.record_size
        self.file = _open_create(self.path,  size)
        fileno = self.file.fileno()
        self.map = mmap.mmap(fileno, size)
        return self

    def close(self):
        if (self.map):
            self.map.close()
            self.map = None
            
        if (self.file):
            self.file.close()
            self.file = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
    
    def __getitem__(self, key):
        if not self.file:
            return None
        offset = key * self.record_size
        ret = self.instance_clazz.from_buffer(self.map, offset)

        return ret
    
