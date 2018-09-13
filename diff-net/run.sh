#!/bin/bash -e
cur=`date +%s`.xml
get-net ../topology.xml $cur
sleep 10
prev=$cur

cur=`date +%s`.xml
get-net ../topology.xml $cur

if [ "$prev" != "" ] ; then
  echo diff-net $prev $cur
  diff-net $prev $cur
fi

#extra fancy way to find the first $cur
#prev=`ls *.xml | sort -n | tail -n 1`

