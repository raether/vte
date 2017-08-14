#!/bin/bash
cpuTemp0=$(cat /sys/class/thermal/thermal_zone0/temp)
cpuTemp1=$(($cpuTemp0/1000))
cpuTemp2=$(($cpuTemp0/100))
cpuTempM=$(($cpuTemp2 % $cpuTemp1))
GPU=`/opt/vc/bin/vcgencmd measure_temp`
echo CPU temp "=" $cpuTemp1"."$cpuTempM"'C   ---  " GPU $GPU 
