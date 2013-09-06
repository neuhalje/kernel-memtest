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

class MmapWrapper(object):
    '''
    Extends the mmap base class by implementing the methods used for with "with"
    '''


    def __init__(self, mmap):
        '''
        Constructor: mmap is an instance of mmap.mmap
        '''
        self.__mmap = mmap

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.__mmap:  self.__mmap.close()
             
    def __getattr__(self, name):
        "Delegate pattern"
        return getattr(self.__mmap, name)
        
    def __getitem__(self, index):
        if  not (index  == self.__mmap.tell()):
            self.__mmap.seek(index)
            
        return ord(self.__mmap.read_byte())
        
                
    def __setitem__(self, index,value):
        if  not (index  == self.__mmap.tell()):
            self.__mmap.seek(index)
            
        self.__mmap.write_byte(chr(value))