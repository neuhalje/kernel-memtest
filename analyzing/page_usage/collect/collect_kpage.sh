#!/bin/bash
#
# Collect the usage data of physical memory from /proc/kpagecount and /proc/kpageflags
#
# Both files are documented in (Kernel source)/Documentation/vm/pagemap.txt
#
# This skript periodically dumps the content of these files.
#
# The script accepts two arguments
#
#   The time to wait between dumps
#   The numer of dumps to make
#    
# Example:
#  $0 /tmp 2 10
# Take 10 snapshots of /proc/kpage(count|flags) and wait 2 seconds between the (pair of) dumps
#
# The script emmits the files created on stdout:
#     $ ./collect_kpage.sh /tmp 4 2
#     /tmp/devel_kpageflags@1269616462.bin
#     /tmp/devel_kpagecount@1269616462.bin
#     
#     /tmp/devel_kpageflags@1269616466.bin
#     /tmp/devel_kpagecount@1269616466.bin
#
#
# The format of the filename is HOST_file@seconds since epoch.bin
#


SLEEPTIME=1

if [ $1 ]
then
outdir=$1
else
outdir=.
fi

if [ $2 ]
then
	if [ ! $(echo "$2" | grep -E "^[0-9]+$") ]
	then
		echo $2 is not a valid integer.
		exit 1
	else
		SLEEPTIME=$2
	fi
fi

NUM_SNAPSHOTS=-1
if [ $3 ]
then
	if [ ! $(echo "$3" | grep -E "^[0-9]+$") ]
	then
		echo $3 is not a valid integer.
		exit 1
	else
		NUM_SNAPSHOTS=$3
	fi
fi

# Blocksize for DD
# Faster than the default
BLOCKSIZE=1M

# The current date in seconds since epoch
postfix_generator="date +%s"

function dump
{
        postfix=$($postfix_generator)
	for file in /proc/kpageflags /proc/kpagecount
	do
	 outfile_name=$(hostname -s)_$(basename $file)@${postfix}.bin
         outfile=$outdir/$outfile_name
	 dd if=$file of=$outfile bs=$BLOCKSIZE 2>/dev/null 1>/dev/null
         echo $outfile
	done
}

i=0

while [ $i -ne $NUM_SNAPSHOTS ]
do
	sleep $SLEEPTIME
	dump
	echo
	i=$((i+1))
done
