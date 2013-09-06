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

import re

class FileSetsByRegexp:
    """
    Groups a list of filenames by an id extracted from the filename.
    """
    def __init__(self, id_regexp_s, id_group = 0):
        self.id_regexp = re.compile( id_regexp_s)
        self.id_regexp_s = id_regexp_s
        self.id_group = id_group
        
    def extract_id(self, name):
        ret = None
        
        s = self.id_regexp.search(name)
        
        if s:
            groups = s.groups()
            if groups:
                ret =  groups[self.id_group]
        
        return ret
        
    def group_by(self, list_of_names):
        """ Return a dictionary of id -> [files]  that
            is grouped by applying `extract_id` to the filenames
        """
        groups = {}
        for name in list_of_names:
            id = self.extract_id(name)
            
            if id:
                if groups.has_key(id):
                    groups[id].append(name)
                else:
                    groups[id] = [name]
            else:
                print("Ignoring name '%s" % (name,))
        return groups
    
    
class FileSetIterator:
      
    def __init__(self, files, filename_regexp = r'^.*kpage([^@]+)@(\d+)\.bin$', group_timestamp = 1, group_type = 0):
        self.filename_regexp = filename_regexp
        
        self.by_timestamp = FileSetsByRegexp(filename_regexp,group_timestamp)
        self.by_type = FileSetsByRegexp(filename_regexp,group_type)
        self.files = files
        
    def __iter__(self):
        self.sets =  list(self.by_timestamp.group_by(self.files).itervalues())
        self.index = 0
        return self
    
    def next(self):
        return self.__next__()
    
    def __next__(self):
        """
        return (flags_file, count_file)
        """
        if self.index == len(self.sets):
            raise StopIteration
        
        current_set = self.sets[self.index]
        grouped_set = self.by_type.group_by(current_set)

        flags_file = grouped_set['flags'][0]
        count_file = grouped_set['count'][0]
        
        ret = (flags_file, count_file)
        self.index += 1
        return ret
 

    