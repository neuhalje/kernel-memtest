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
from physmem import Physmem
from physmem import Phys_mem_frame_request
from physmem import Phys_mem_request
from physmem import Phys_mem_frame_status

from physmem import Mark_page_poison

from physmem import PAGE_SIZE

from physmem import SOURCE_FREE_PAGE
from physmem import SOURCE_FREE_BUDDY_PAGE
from physmem import SOURCE_PAGE_CACHE
from physmem import SOURCE_ANONYMOUS
from physmem import SOURCE_ANY_PAGE
from physmem import SOURCE_HW_POISON_ANON
from physmem import SOURCE_HW_POISON_PAGE_CACHE

