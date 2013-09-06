Content
========

This directory contains the userspace parts of the memory tester, namely the scheduler that decides which memory frame to test (and how), and two dummy implementations of test algorithms. For a production scenario the test algorithms would be written in C or assembler, not python.

The implementation uses `/dev/phys_mem` (implementation of kernel module in  ../physmem) to access physical memory. It also contains an adapter that converts Python methods into `ioctl`s.

Example
--------

```
$ # start the memory test
$ ./main.py
0x230000 frames (2293760 decimal), of which are 945815 tested (41.2 %) and 1347945 untested (58.8 %), 0 have seen errors.
For tested frames, the following statistics have been calculated:
Time it took to claim a frame (in jiffies) (min,max,avg) : 0, 1, 0
Timestamp of last test (min,max,avg) : 2010-06-03 22:30:22, 2010-06-04 11:23:32, 2010-06-04 05:03:00
...
^C KeyboardInterrupt $ ./main.py
0x230000 frames (2293760 decimal), of which are 945899 tested (41.2 %) and 1347861 untested (58.8 %), 0 have seen errors.
For tested frames, the following statistics have been calculated:
Time it took to claim a frame (in jiffies) (min,max,avg) : 0, 1, 0
Timestamp of last test (min,max,avg) : 2010-06-03 22:46:30, 2010-06-13 12:34:09, 2010-06-04 05:42:36
```
