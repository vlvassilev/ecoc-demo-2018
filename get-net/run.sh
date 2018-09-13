#!/bin/bash -e
prev=`ls *.xml | sort -n | tail -n 1`
cur=`date +%s`.xml
get-net ../topology.xml $cur
if [ "$prev" != "" ] ; then
  echo diff-net $prev $cur
  diff-net $prev $cur
fi
