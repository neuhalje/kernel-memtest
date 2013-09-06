## Summary

Everything a computer does at some point involves RAM ("Memory"). Typical home computers, and small servers have between 4 and 16 gigabytes of it. Defects RAM is not easily detected because the symptoms are very unspecific. But in almost all cases bad RAM corrupts data that is saved to disk at some point. Corrupted data can be anything between a pixel in a video having a slightly different color than is should, documents/databases that are no longer readable, or -- worst -- data that you or your company is liable for has changed its meaning without anyone finding out until it is too late.

In mid 2009 Google and Bianca Schroeder from the University of Toronto published [a study](http://research.google.com/pubs/pub35162.html)  that showed that Google’s -- albeit commodity grade -- server hardware is prone to memory errors: *Each year a third of the studied systems suffered at least on correctable memory error (CE)*. According to their study, a system that had a CE in the past is very likely to have much more CEs or even uncorrectable errors (UE) in the near future.
It is safe to assume, that consumer grade hardware is likely to show worse behaviour. These results emphasize the importance of the early detection of defective memory modules.

Not only Google found this out: From the [NASA website](http://www.jpl.nasa.gov/news/news.php?release=2010-151), updated May 17, 2010 at 5:00 PT.
<blockquote>
One flip of a bit in the memory of an onboard computer appears to have caused the change in the science data pattern returning from Voyager 2, engineers at NASA’s Jet Propulsion Laboratory said Monday, May 17. A value in a single memory location was changed from a 0 to a 1. 
</blockquote>


### TL;DR

Broken RAM is bad. Finding defect RAM is a non trivial task, and can be done in hardware (e.g. ECC memory), software (e.g. [memtest86+](http://www.memtest.org/)) or a combination of both. Hardware tests do not find all errors, and conventional software tests require many hour long downtimes of the machines. Other software tests can run while the computer is in normal use, e.g. editing spreadsheets or serving webpages. These programs have a different problem: They just randomly poke around the computer memory, and often test only very small parts of the system memory.

In my diploma thesis I developed an online memory test for the Linux kernel. This is a program (userspace & kernel module) that can test substantial (~70%, more with some programming) parts of the computers memory while the computer is in normal use, thus solving the biggest current problem with memory test. 

### More?

If you want to know more, then read my [blogpost](http://www.neuhalfen.name/2013/09/05/your-data-is-corrupted-and-you-dont-know-it/). If that still is not enough, read the [thesis](thesis).

## Content

![*Package Diagram of the Design* The package diagram of the implementation shows seven packages, six of them are a part of the implementation.  The `TestScheduler` on the left side determines which frames are to be tested when, and how. Algorithms for different fault models are implemented according to the strategy pattern. Kernel based services are located in the middle column. At the top is the `StructPageMap` package that allows user space processes to mmap the page-flags into their address room. Below it are the Linux kernel and the `PhysMem` module which implements the functionality, giving the user space access to the frames acquired by the `PageClaiming` Implementations.  On the right side, the `MemoryVisualization` package can collect snapshots of the pageflags and generate videos that visualize the behaviour of the mm.](assets/Packages.png)

The implementation has three major parts:

* A [kernel module](physmem/kernel/module/) that allows user space programs to request, and isolate specific page frames.
* A userspace [implementation that drives the test](memtester/): It decides which frame to test when, and how.
* Userpace implementations that implement the test algorithms to test a single page frame.

Further there are some tools to analyse the memory management:

* [Analyze changes in the Linux source code](analyzing/mm-diff).
* [Collect and visualize runtime behaviour of the Linux mm](analyzing/page_usage).
