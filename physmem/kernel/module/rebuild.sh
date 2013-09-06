#!/bin/bash
sudo chmod 444 /proc/kpage*
sudo rmmod phys_mem
make && sudo insmod phys_mem.ko && sudo chmod 777 /dev/phys_mem && echo OK

