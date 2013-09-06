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
import os.path

class DataSource:
    """
     Reads a (binary) file consisting of records and provides an
     iterator-style interface.
     
     Life-cycle:
     
     1) Create DataSource `ds`
     2) call `ds.open`
     3) call `ds.next_record`. On EOF `None`is returned. 
        The object returned is a tupel parsed by calling `struct.unpack(...)`
     4) close by calling `ds.close`
     
     Each record is  read by calling the `next_record` method which internally
     calls `_get_record_size` to determine the size of the to-be read record
     and then `_parse_record` to convert the record into the target class.
     
     Classes deriving from `DataSource` can override `_get_record_size` and 
     `_parse_record` to provide custom target types.
     
    """
    
    def __init__(self, name, path, record_format):
        self.path = path
        self.record_format = record_format
        self.type = name
        self.record_size = self._get_record_size()
        self.file = None

    def get_record_count(self):
        """
        Return the number of records in the file, IFF the file supports  os.path.getsize correctly.
        E.g. "/proc/kpageflags" does NOT support this correctly
        """
        return  os.path.getsize(self.path) /  self._get_record_size()
        
    def _get_record_size(self):
        return struct.calcsize(self.record_format) 

    def _parse_record(self, chunk):
        return struct.unpack(self.record_format, chunk) 

    def _get_open_file(self):
        if (not self.file):
            self.open()
        return self.file
    
    def open(self):
        self.close()
        self.file = open(self.path,'rb')
        return self

    def close(self):
        if (self.file):
            self.file.close()
            self.file = None

    def next_record(self):
        if not self.file:
            return None

        chunk = self.file.read(self.record_size)
        if chunk:
            record = self._parse_record(chunk)
            return record
        else:
            return None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
    
    def __getitem__(self, key):
        if not self.file:
            return None
        offset = key * self.record_size
        self.file.seek(offset)
        return self.next_record()

class ConstantDataSource():
    
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def open(self):
        return self

    def close(self):
        pass
    
    def next_record(self):
        return self.value

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass    
