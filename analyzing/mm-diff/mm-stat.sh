#!/bin/bash

# For each released kernel version (tag), this script prints some metrics (Kernel Version, size of the subsystem, number of files, linecount, number of #ifdefs).
#
# Run from the top of the kernel sources git repository.
# argument: The subsystem (directory) to analyse, e.g. "mm"

IGNORED='.*rc.*'


if [ ! "$1" = "" ]
then
  SUBSYSTEM_SELECTOR="$1"
  echo "Subsystem: $1"
else
  SUBSYSTEM_SELECTOR="."
  echo "The whole kernel"
fi

echo "Revision,  size in kb, number of files, linecount, number of ifdefs"

git tag -l| while read current; 
 do 

     echo $current| grep -q -s -v  $IGNORED 
     ignore=$?
     if [ $ignore -eq 0 ]
     then
                git reset --hard -q
                git checkout -q -f $current -- $SUBSYSTEM_SELECTOR
                size_in_k=$(du -s --apparent-size  $SUBSYSTEM_SELECTOR|sed 's/\([0-9]*\).*$/\1/')
                files=$(find $SUBSYSTEM_SELECTOR -type f| wc -l)
                lines=$(find $SUBSYSTEM_SELECTOR -type f -print0| wc -l --files0-from=- | grep '^[0-9]* total$'|sed 's/\([0-9]*\).*$/\1/')
                ifdefs=$(grep -R -E 'if[n]?def' $SUBSYSTEM_SELECTOR |wc -l)

    echo  "$current, $size_in_k, $files, $lines, $ifdefs"
    fi
 done 
