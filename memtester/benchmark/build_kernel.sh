#!/bin/bash


for tst in memstress tightloop
do
echo $tst

TEST=normal

cd /home/jens/work/kernel/
make clean
sync

cd /home/jens/work/pages/memtester/benchmark/micro
./$tst  &
MT=$!
sleep 5

cd /home/jens/work/kernel/
time  (make -j2 1>/dev/null) 2>/home/jens/work/pages/memtester/benchmark/kernel-${TEST}-${tst}.log 

kill $MT
 # -------------------


TEST=nice

cd /home/jens/work/kernel/
make clean
sync

cd /home/jens/work/pages/memtester/benchmark/micro
nice -n 20 ./$tst &
MT=$!
sleep 5

cd /home/jens/work/kernel/
time  (make -j2 1>/dev/null) 2>/home/jens/work/pages/memtester/benchmark/kernel-${TEST}-${tst}.log 

kill $MT
 # -------------------
done
exit
