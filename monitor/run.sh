#!/bin/bash -e
period=20000000000
mv 11.xml 12.xml | true
mv 10.xml 11.xml | true
mv 9.xml 10.xml | true
mv 8.xml 9.xml | true
mv 7.xml 8.xml | true
mv 6.xml 7.xml | true
mv 5.xml 6.xml | true
mv 4.xml 5.xml | true
mv 3.xml 4.xml | true
mv 2.xml 3.xml | true
mv 1.xml 2.xml | true
mv prev.xml 1.xml | true
mv cur.xml prev.xml | true
cur_nanoseconds=`date +%s%N`
ns_since_last_checkpoint=`echo "${cur_nanoseconds}%${period}" | bc`
echo $ns_since_last_checkpoint
sleep_time=`echo "scale=4; (${period}-${ns_since_last_checkpoint})/1000000000" | bc`
echo "Sleeping for ${sleep_time} sec."
sleep $sleep_time
date
get-net ../topology.xml cur.xml

#echo '<html><head></head><body><p><tt>' | tee report.html
echo '<link href="txtstyle.css" rel="stylesheet" type="text/css" />' | tee report.html
echo "Report time: `date +%H:%M:%S`" | tee  report.txt
echo "" | tee -a report.txt
python report.py prev.xml cur.xml | tee -a report.txt
#echo '</tt></p></body></html>'  | tee -a report.html
#txt2html report.txt > report.html
./traffic-graphic-ecoc-demo --background=../topology-wo-traffic.svg --before=prev.xml --after=cur.xml --output=topology-w-indicators.svg
