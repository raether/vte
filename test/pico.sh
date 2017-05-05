#!/bin/sh
#
# (Al) - hmm.tricky@gmail.com

# Script to use the UPS PIco to cool the Pi, run on battery power for a set period
# and initiate a shutdown as required.

  version="2-0.92"

  fcount=0
  fcount_max=4

  pico_bat_runtime=60
  bat_mode=1
  mode_count=1
  start_secs=`date +%s`
  bat_count=60

  pico_battery=0
  pico_fan="no"
  temp_count=0
  pico_temp1_speed="60"
  pico_temp2_speed="67"
  pico_temp3_speed="73"
  pico_temp4_speed="77"
  pico_reset="no"

  global_rc="/root/scripts/global.rc"
  main_dir="/home/camera"
  usb_directory="$main_dir/usb"
  status_dir="$main_dir/logs"
  status_file="status.txt"
  status_out="$status_dir/$status_file"
  shutdown_method="pios"
  home_enabled="no"

  usb_device="/dev/sda1"
  usb_mount="yes"
  i2c_number=1

  bat_highest=420
  bat_lowest=330
  bat_100=""
  bat_100_count=0

check_globals()
{
	if [ -f $global_rc ]; then
	 tmp_glob="`grep log_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then
	  status_dir="$tmp_glob"
	  status_out="$status_dir/$status_file"
	 fi
	 tmp_glob="`grep main_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then main_dir="$tmp_glob"; fi
	 tmp_glob="`grep shutdown_method $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then shutdown_method="$tmp_glob"; fi
	 tmp_glob="`grep usb_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then usb_directory="$tmp_glob"; fi

	 tmp_glob="`grep pico_bat_runtime $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_bat_runtime="$tmp_glob"; fi
	 tmp_glob="`grep pico_fan $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_fan="$tmp_glob"; fi
	 tmp_glob="`grep pico_temp1_speed $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_temp1_speed="$tmp_glob"; fi
	 tmp_glob="`grep pico_temp2_speed $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_temp2_speed="$tmp_glob"; fi
	 tmp_glob="`grep pico_temp3_speed $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_temp3_speed="$tmp_glob"; fi
	 tmp_glob="`grep pico_temp4_speed $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_temp4_speed="$tmp_glob"; fi
	 tmp_glob="`grep pico_reset $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then pico_reset="$tmp_glob"; fi

	 tmp_glob="`grep home_enabled $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_enabled="$tmp_glob"; fi
	fi
}
	check_globals

	tmp_glob="`grep usb_device $global_rc | grep -v ^# | awk '{print$2}'`"
	if [ ! -z "$tmp_glob" ]; then usb_device="$tmp_glob"; fi
	if [ "$usb_mount" = "yes" ] && [ ! -z `mount | grep "$usb_device" | awk '{print $1}'` ]; then
	 global_rc="$usb_directory/global.rc"
	 if [ -f $global_rc ]; then
	  check_globals
	 fi

	 touch "$status_out" > /dev/null 2>&1
	 status=$?
	 if [ $status -ne 0 ]; then
	  old_status_dir="$status_dir"
	  status_dir="$main_dir/logs"
	  status_out="$status_dir/$status_file"
	  printf "`date +%T` [pico]: * Write failed for $old_status_dir using $status_dir *\n" >> $status_out
	 fi
	fi

stop_pico()
{
        printf "`date +%T` [pico]: Stopped.\n" >> $status_out
	if [ "$pico_fan" = "yes" ]; then
	 i2cset -y $i2c_number 0x6B 16 0
	 i2cset -y $i2c_number 0x6B 15 0
	fi
	exit 0
}

bat_percent()
{
	bat_mode="$((`i2cget -y $i2c_number 0x69 0`))"
	batlevel=`i2cget -y $i2c_number 0x69 1 w`
	battery_level="`printf '%x' $batlevel`"
	bat_min_low="`echo - | awk '{printf '$battery_level' - '$bat_lowest'}'`"
	high_min_low="`expr $bat_highest - $bat_lowest`"
	sum="`echo - | awk '{printf '$bat_min_low' / '$high_min_low'}'`"
	percent="`echo - | awk '{printf \"%.0f\", '$sum' * 100}'`"
	if [ $percent -gt 100 ]; then
	 percent=100
	elif [ $percent -lt 0 ]; then
	 percent=0;
	fi
}

pico_temp()
{
	temp="`expr \`cat /sys/class/thermal/thermal_zone0/temp\` / 1000`"
        temp_SoC="`/opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}' | cut -d. -f1`"
	tmpcels="`i2cget -y 1 0x69 0x0C | cut -dx -f2`"
	tmpcelt="`i2cget -y 1 0x69 0x0D | cut -dx -f2`"

	fspeed="$((`i2cget -y $i2c_number 0x6B 16`))"
	if [ $temp -gt $pico_temp4_speed ]; then
	 if [ $fspeed -ne 1 ] && [ $fcount -eq 0 ]; then
	  printf "`date +%T` [pico]: Temperature is $temp. Fan ON 100%%\n" >> $status_out
	  i2cset -y $i2c_number 0x6B 16 1
	 fi
	elif [ $temp -gt $pico_temp3_speed ]; then
	 if [ $fspeed -ne 4 ] && [ $fcount -eq 0 ]; then
	  printf "`date +%T` [pico]: Temperature is $temp. Fan ON (75%%)\n" >> $status_out
	  i2cset -y $i2c_number 0x6B 16 4
	 fi
	elif [ $temp -gt $pico_temp2_speed ]; then
	 if [ $fspeed -ne 3 ] && [ $fcount -eq 0 ]; then
	  printf "`date +%T` [pico]: Temperature is $temp. Fan ON (50%%)\n" >> $status_out
	  i2cset -y $i2c_number 0x6B 16 3
	 fi
	elif [ $temp -gt $pico_temp1_speed ]; then
	 if [ $fspeed -ne 2 ] && [ $fcount -eq 0 ]; then
	  printf "`date +%T` [pico]: Temperature is $temp. Fan ON (25%%)\n" >> $status_out
	  i2cset -y $i2c_number 0x6B 16 2
	 fi
	elif [ $fspeed -gt 0 ] && [ $fspeed -le 4 ] && [ $fcount -ge $fcount_max ]; then
	  printf "`date +%T` [pico]: Switching fan OFF\n" >> $status_out
	  i2cset -y $i2c_number 0x6B 16 0
	  fcount=0
	fi
	fcount=`expr $fcount + 1`
	if [ $fcount -gt $fcount_max ]; then fcount=0; fi
}

	trap 'stop_pico' INT TERM USR1
	i2cset -y $i2c_number 0x6B 9 0xff

	if [ "$pico_reset" = "yes" ]; then
	 printf "`date +%T` [pico]: Resetting...\n" >> $status_out
	 i2cset -y $i2c_number 0x6B 0 0xee
	 sleep 15
	fi

	printf "`date +%T` [pico]: Started (v$version). Battery runtime set to $pico_bat_runtime seconds\n" >> $status_out
	if [ "$pico_fan" = "yes" ]; then
	 i2cset -y $i2c_number 0x6B 16 0;i2cset -y $i2c_number 0x6B 15 1
	fi
	sleep 5

	while true
	 do
	  bat_percent
	  if [ $percent -lt 100 ]; then
	   bat_count=`expr $bat_count + 1`
	   if [ $bat_count -gt 30 ]; then
	    printf "`date +%T` [pico]: Battery estimated at $percent%%\n" >> $status_out
	    bat_count=0
	    bat_100=""
	    bat_100_count=0
	   fi
	  else
	   if [ "$bat_100" = "" ] && [ $bat_100_count -gt 2 ]; then
	    printf "`date +%T` [pico]: Battery at $percent%%\n" >> $status_out
	    bat_100="True"
	   else
	    bat_100_count=`expr $bat_100_count + 1`
	   fi
	  fi

	  if [ "$pico_fan" = "yes" ]; then pico_temp; fi
	  if [ $temp_count -ge 16 ]; then
	   printf "`date +%T` [pico]: CPU: $temp˚C  BC: $temp_SoC˚C  SOT-23: $tmpcels˚C  TO-92: $tmpcelt˚C\n" >> $status_out
	   temp_count=0
	  else
	   temp_count=`expr $temp_count + 1`
	  fi

	  if [ $bat_mode -eq 1 ]; then
	   start_secs=`date +%s`
	   if [ $pico_battery -gt 0 ]; then
	    printf "`date +%T` [pico]: Power source restored. Battery estimated at $percent%%\n" >> $status_out
	    mode_count=1
	    pico_battery=0
	   fi
	  elif [ $bat_mode -eq 2 ]; then
	   if [ $mode_count -ge 2 ]; then
	    if [ $pico_battery -eq 0 ]; then printf "`date +%T` [pico]: Power source removed, using battery ($percent%%). Shutdown in $pico_bat_runtime seconds\n" >> $status_out
	     pico_battery=1
	    fi
 	    end_secs=`date +%s`
	    if [ `expr $end_secs - $start_secs` -ge $pico_bat_runtime ] && [ $pico_battery -eq 1 ]; then
	     printf "`date +%T` [pico]: Reached $pico_bat_runtime seconds, initiating shutdown\n" >> $status_out
	     pico_battery=2
#	     if [ "$shutdown_method" = "pico" ]; then
#	      if [ "$home_enabled" = "yes" ]; then /root/scripts/home.sh; fi
#	      printf "`date +%T` [pico]: Shutting down now ($shutdown_method)\n" >> $status_out
#	      i2cset -y $i2c_number 0x6B 0 0xcc
#	     else
	      pkill -SIGUSR1 pwr_butt
#	      printf "`date +%T` [pico]: Stopped\n" >> $status_out
#	     fi
#	    exit
	    fi
	   else
	    mode_count=`expr $mode_count + 1`
	   fi
	  fi
	 sleep 5
	done
