#!/bin/sh

display_temperature="`ssh $1 /opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}'`"
temperature="`ssh $1 cat /sys/class/thermal/thermal_zone0/temp`"
cpu_speed="`ssh $1 cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`"
display_cpu_speed="`expr $cpu_speed / 1000`Mhz"
uptime_info="`ssh $1 uptime | cut -c11-80`"
root_disk_usage="`ssh $1 df -h | grep root | awk '{print $5}'`"
data_disk_usage="`ssh $1 df -h | grep mmcblk0p3 | awk '{print $5}'`"

echo "Temperature $display_temperature"
echo "Thermal Temperature $temperature"
echo "CPU Speed $cpu_speed"
echo "Display CPU Speed $display_cpu_speed"
echo "Uptime $uptime_info"
echo "Root Disk Usage $root_disk_usage"
echo "Data Disk Usage $data_disk_usage"
