#!/bin/bash


# For each released kernel version (tag), this script prints some metrics (Revision, files changed, insertions, deletions).
#
# Run from the top of the kernel sources git repository.
# argument: The subsystem (directory) to analyse, e.g. "mm"

IGNORED='.*rc.*'

if [ ! "$1" = "" ]
then
  SUBSYSTEM_SELECTOR="-- $1"
  echo "Subsystem: $1"
else
  echo "The whole kernel"
fi

echo "Revision,  files changed, insertions(+), deletions(-)"

git tag -l| while read current; 
 do

     echo $current| grep -q -s -v  $IGNORED 
     ignore=$?
     if [ $ignore -eq 0 ]
     then
       if [ "$last" != "" ]; 
         then 
       stat=$(git diff $last $current --shortstat $SUBSYSTEM_SELECTOR)
       if [ "$stat" != "" ]
       then
    echo  "$current, $stat" | sed -e 's/files changed//;s/insertions...//;s/deletions...//g'
       fi
        else
    echo "$current,0,0,0"
        fi
        last=$current
    fi
 done 
