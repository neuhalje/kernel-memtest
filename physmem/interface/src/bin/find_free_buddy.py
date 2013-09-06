#!/bin/env python

from kpage  import *
import physmem

def find_free_buddy_pfns(pageflags, max_hits):
    ret =[]
    pfn = 0
    with pageflags.open() as pf:
        while max_hits:
                flags = pf.next_record()
                if  (None == flags):
                    break
                
                if (flags.all_set_in(kpageflags.BUDDY)):
                    ret.append( pfn)     
                    max_hits -= 1
                pfn += 1
    return ret

pageflags = kpageflags.FlagsDataSource(kpageflags.KPageFlags, "/proc/kpageflags")

max_hits = 50

buddies  = find_free_buddy_pfns(pageflags, 50)

print(buddies)
print("Done")            
