#!/bin/sh

TEST=$1

cd /home/jens/work/kernel/
make clean
sync
cd /home/jens/work/pages/memtester/scheduler/src

cd /home/jens/work/pages/memtester/scheduler/src
python -u -O main.py > /home/jens/work/pages/memtester/benchmark/kernel-${TEST}-python.log &
MT=$!

sleep 10

cd /home/jens/work/kernel/
time -o/home/jens/work/pages/memtester/benchmark/kernel-${TEST}-kernel.log & make 1>/dev/null

sleep 5

kill $MT
tail /home/jens/work/pages/memtester/benchmark/kernel-${TEST}-python.log
tail /home/jens/work/pages/memtester/benchmark/kernel-${TEST}-kernel.log
