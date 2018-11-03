#!/bin/bash
#
#/root/bin/sensors.sh
# The hard-coded script name here is a potential issue, but $0 fails, and we need bash to print the degree symbols
# sensors.sh
# A script to display Raspberry Pi on-board sensor data
#
# LGD: Mon Dec 23 04:07:23 PST 2013
# LGD: Mon Aug 10 14:02:46 PDT 2015: Added degree symbols, over-temperature based on degrees C so it will work without bc 
#

TEMPC=$(/opt/vc/bin/vcgencmd measure_temp|awk -F "=" '{print $2}')	# Get Temp C
TEMPf=$(echo -e "$TEMPC" | awk -F "\'" '{print $1}' 2>/dev/null)	# Get numeric-only Temp C
TEMPF=$(echo "scale=2;${TEMPf}*9/5+32"|bc -l)				# Calculate Temp F
ALRM=""
[ `echo $TEMPC|cut -d. -f1` -gt 70 ] && ALRM=" TOO HOT! "		# Check for over-temp: Max = 70C or 158F
TEMPB4OVER=$(echo "70-${TEMPf}"|bc -l)

[ `type bc 2>&1 >/dev/null` ] && echo -e "Binary Calculator package (bc) not found.  Fahrenheit temperatures will not be displayed\n" # BUG: this test fails to work as desired 
#echo -e "\nThe BCM2835 SoC (CPU/GPU) temperature is: ${TEMPF}'F (${TEMPC}) `tput smso`$ALRM`tput rmso`"
echo -e "\nThe BCM2835 SoC (CPU/GPU) temperature is: ${TEMPF}\xc2\xb0 F\t(${TEMPf}\xc2\xb0 C) `tput smso`$ALRM`tput rmso`"
echo -e "\t\t70\xc2\xb0 C HIGH-TEMP LIMIT will be reached in ${TEMPB4OVER}\xc2\xb0 C higher" 

echo -e "\nThe Core voltage is: \c"
/opt/vc/bin/vcgencmd measure_volts core|awk -F "=" '{print $2}'

echo -e "\nThe sdram Core voltage is: \c"
/opt/vc/bin/vcgencmd measure_volts sdram_c|awk -F "=" '{print $2}'
     
echo -e "\nThe sdram I/O voltage is: \c"
/opt/vc/bin/vcgencmd measure_volts sdram_i|awk -F "=" '{print $2}'

echo -e "\nThe sdram PHY voltage is: \c"
/opt/vc/bin/vcgencmd measure_volts sdram_p|awk -F "=" '{print $2}'
echo

exit


Not Reached
========================================================
On-board Hardware Sensors

Temperature

   Temperatures sensors for the board itself are included as part of the raspberry pi-firmware-tools package.
   The RPi offers a sensor on the BCM2835 SoC (CPU/GPU):
	/opt/vc/bin/vcgencmd measure_temp
	temp=49.8'C

   Alternatively, simply read from the filesystem: /sys/devices/virtual/thermal/thermal_zone0 
	cat /sys/class/thermal/thermal_zone0/temp
	49768

   For human readable output:
	awk '{printf "%3.1fM-0C\n", $1/1000}' /sys/class/thermal/thermal_zone0/temp
	54.1M-0C

Voltage

   Four different voltages can be monitored via /opt/vc/bin/vcgencmd as well:
% /opt/vc/bin/vcgencmd measure_volts <id>

     * core for core voltage
     * sdram_c for sdram Core voltage
     * sdram_i for sdram I/O voltage
     * sdram_p for sdram PHY voltage

--------------------
Output: 

The BCM2835 SoC (CPU/GPU) temperature is: temp=44.9'C

The Core voltage is: volt=1.20V

The sdram Core voltage is: volt=1.20V

The sdram I/O voltage is: volt=1.20V

The sdram PHY voltage is: volt=1.23V
==============================
See: man sensord sensor.conf
==================================================

˚
echo $'\xc2\xb0'C 	# Works in ksh and bash
echo -e "\0302\0260"	# Works in ksh and bash

http://stackoverflow.com/questions/8334266/how-to-make-special-characters-in-a-bash-script-for-conky

to enter from keyboard:
Ctrl-Shift u + 00b0


˚	RING ABOVE (U+02DA)	feff02da

/root (/dev/pts/0) # echo -e "°"
°
/root (/dev/pts/0) # echo -e "°"|hexdump -c
0000000   �   �  \n                                                    
0000003

/root (/dev/pts/0) # echo -e "°"|hexdump 
0000000 b0c2 000a                              
0000003

/root (/dev/pts/0) # 
DEGCEL="\0260C"; echo -e $DEGCEL
°C
====================================================================
