collect_kpage.sh
=================

Collect the usage data of physical memory from `/proc/kpagecount` and `/proc/kpageflags`, and periodically dumps the content of these files.

These files are then fed into `../analyzing/flag_painter.py` to create images/videos of the page usage.


Both files (`kpage*`) are documented in (Kernel source)/Documentation/vm/pagemap.txt


Example:
---------
The script accepts two arguments

1. The time to wait between dumps
2. The numer of dumps to make

`$0 /tmp 2 10`

Take 10 snapshots of /proc/kpage(count|flags) and wait 2 seconds between the (pair of) dumps

The script emmits the files created on stdout:
```bash
$ ./collect_kpage.sh /tmp 4 2
/tmp/devel_kpageflags@1269616462.bin
/tmp/devel_kpagecount@1269616462.bin

/tmp/devel_kpageflags@1269616466.bin
/tmp/devel_kpagecount@1269616466.bin
```


The format of the filename is `HOST_file@seconds since epoch.bin`.

