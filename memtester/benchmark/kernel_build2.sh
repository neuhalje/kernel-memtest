#!/bin/bash


tst=MemTest
echo $tst

 # -------------------


TEST=nice

cd /home/jens/work/kernel/
make clean
sync

cd /home/jens/work/pages/memtester/scheduler/src
nice -n 20 python -u -O main.py > /home/jens/work/pages/memtester/benchmark/kernel-${TEST}-python.log &

MT=$!
sleep 5

cd /home/jens/work/kernel/
time  (make -j2 1>/dev/null) 2>/home/jens/work/pages/memtester/benchmark/kernel-${TEST}-${tst}.log 

kill $MT
 # -------------------
