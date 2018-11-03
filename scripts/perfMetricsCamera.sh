#!/bin/sh

mhostname="`hostname`"
display_temperature="`/opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}'`"
temperature="`cat /sys/class/thermal/thermal_zone0/temp`"
cpu_speed="`cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`"
display_cpu_speed="`expr $cpu_speed / 1000`Mhz"
uptime_info="`uptime -s`"
root_disk_usage="`df -h | grep root | awk '{print $5}'`"
data_disk_usage="`df -h | grep mmcblk0p3 | awk '{print $5}'`"
cpu_usage="`top -b -n1 | grep "Cpu(s)" | awk '{print $2 + $4}'`"
memory_data_string="`free -m | grep Mem`"
used_memory="`echo $memory_data_string | cut -f3 -d' '`"
total_memory="`echo $memory_data_string | cut -f2 -d' '`"
memory_usage="`echo "scale=2; $used_memory/$total_memory*100" | bc`"
voltage="`/opt/vc/bin/vcgencmd measure_volts | awk -F "=" '{print$2}'`"
local_ip="`/sbin/ifconfig eth0 | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p'`"
wireless_ip="`/sbin/ifconfig wlan0 | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p'`"


# echo "Temperature     : $display_temperature"
# echo "CPU Speed       : $display_cpu_speed"
# echo "Uptime          : $uptime_info"
# echo "CPU Usage       : $cpu_usage%"
# echo "Memory Usage    : $memory_usage%"
# echo "Root Disk Usage : $root_disk_usage"
# echo "Data Disk Usage : $data_disk_usage"
# echo "Voltage         : $voltage"

echo -n "${mhostname}.local, $local_ip, $wireless_ip, $display_temperature, $display_cpu_speed, $uptime_info, $cpu_usage%, $memory_usage%, $root_disk_usage, $data_disk_usage, $voltage"

