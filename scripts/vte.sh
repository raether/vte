#!/bin/sh
# 
#  Illinois Video Traffice Enforcement
#

#
# ILVTE start up program
#

  version="0.1"

#
#  Set defaults for variables
#
  global_rc="/home/camera/scripts/global.rc"
  main_dir="/home/camera"
  log_dir="$main_dir/logs"
  log_file="status.log"
  status_out="$log_dir/$log_file"

  usb_device="/dev/sda1"
  usb_directory="$main_dir/usb"

  GPS_enabled="yes"
  GPS_wait="yes"
  pi_camera_method="picam"
  picam_enabled="no"
  audio_enabled="no"
  pico_enabled="no"
  button_enabled="no"

  high_temp="81000"
  low_temp="77000"
  over_temp="84000"

  led_2_gpio=4
  use_gpio_leds="no"

  pivid_use_usb="no"
  motion_camera1_use_usb="no"
  audio_use_usb="no"

  root_limit=95
  usb_limit=95
  using_usb=""
  storage_mounted=""
  samba_enabled=""

######################################################
#  Usage:
#     variable_value=$(get_global $1)
#

get_global()
{
        global_var_name=$1
        default_value=$2

        if [ -f $global_rc ]; then
            	return_value="`grep $1 $global_rc | grep -v ^# | awk '{print$2}'`"
		if [ -z "$return_value" ]; then
			return_value=$default_value
		fi
	else
		return_value=$default_balue
        fi

        echo $return_value
}

######################################################
#
#  FUNCTION TO KILL EVERYTHING OFF
#
time_to_die()
{
#
#  Kill all processes associated with ILVTE 
#
	write_log_msg "Stopping..."
	if [ "$pi_camera_method" = "pivid" ]; then
		pkill --signal SIGTERM pivid
	 	sleep 1
	elif [ "$pi_camera_method" = "picam" ]; then
		pkill --signal SIGTERM -f picam.py
		sleep 1
	fi
	if [ "$audio_enabled" = "yes" ]; then
		kill -15 `cat /tmp/audio.pid` > /dev/null 2>&1
		pkill --signal SIGINT arecord
		sleep 1
	fi
	if [ "$pico_enabled" = "yes" ]; then
		pkill --signal SIGTERM -f pico.sh
		sleep 1
	fi
	write_log_msg "Stopped"
exit
}

######################################################

check_usb()
{
	usb_mount=$(get_global "usb_mount")

	if [ "$usb_mount" != "yes" ]; then
		write_log_msg "USB mount disabled in $global_rc"
	 	return
	fi

	usb_mount=$(get_global "usb_device")

	if [ -z "`mount | grep $usb_device`" ]; then
	 if [ -b "$usb_device" ]; then
#	  if [ ! -d "$usb_directory" ]; then
	   mkdir -p "$usb_directory/front" "$usb_directory/rear" "$usb_directory/audio" "$log_dir/tmp" > /dev/null 2>&1
#	  fi
	  mount $usb_device $usb_directory > /dev/null 2>&1
	  status=$?
	  if [ $status -ne 0 ]; then
	   printf "`date +%T` [ilvte]: Failed to mount USB device $usb_device on $usb_directory\n" >> $tmp_stat
	   return
	  else
	   printf "`date +%T` [ilvte]: Mounted $usb_device on $usb_directory\n" >> $tmp_stat
	   df > /dev/null
	   storage_mounted="True"
	  fi
	 else printf "`date +%T` [ilvte]: $usb_device is not available\n" >> $tmp_stat
	 fi
	else
	 printf "`date +%T` [ilvte]: $usb_device already mounted on $usb_directory\n" >> $tmp_stat
         storage_mounted="True"
	fi
	mkdir -p "$usb_directory/front" "$usb_directory/rear" "$usb_directory/audio" "$usb_directory/logs/tmp" > /dev/null 2>&1

	touch "$usb_directory/logs/tmp/.test" > /dev/null 2>&1
	status=$?
	if [ $status -ne 0 ]; then
	 printf "`date +%T` [ilvte]: * Write failed for $usb_directory/logs on $usb_device. Using $main_dir/logs *\n" >> $tmp_stat
#	 umount $usb_device > /dev/null 2>&1
         storage_mounted=""
	 usb_directory="$main_dir"
	 log_dir="$main_dir/logs"
	 status_out="$log_dir/$status_file"
	fi
}

######################################################

write_log_msg()
{
	printf "`date +%T` [ilvte]: $1\n" >> $status_out
}

######################################################

check_globals()
{
#
#  1.  Check if the global.rc file exists.
#  2.  If the global.rc file exists, then overwrite defaults with values in global.rc file.
#  3.  Make sure that variable exists in global.rc before overwriting default.
#

        # check to make sure global.rc file exists
	if [ -f $global_rc ]; then
		#  overwrite variable if it exists in the global.rc file.
		main_dir=$(get_global "main_directory" ${main_dir})
                log_dir=$(get_global "log_directory" ${log_dir})
                status_out="$log_dir/$log_file"
                usb_mount=$(get_global "usb_mount" ${usb_mount})
                usb_device=$(get_global "usb_device" ${usb_device})
                usb_directory=$(get_global "usb_directory" ${usb_directory})
	fi
}

######################################################

start_gpsd()
{
	if [ "$GPS_enabled" = "yes" ]; then
		if [ ! -z "`pgrep gpsd`" ]; then
			write_log_msg "GPS Daemon is already running"
			write_log_msg "`service gpsd status`"
		else 
			write_log_msg "Starting GPS Daemon"
	   		sudo service gpsd restart > /dev/null 2>&1 &
		fi
	fi
}

######################################################

monitor_gpsd()
{
	if [ "$GPS_enabled" = "yes" ]; then
		if [ ! -z "`pgrep gpsd`" ]; then
			gpsd_status="OK"
		else 
			gpsd_status="ERROR"
			write_log_msg "ERROR:  Restarting GPS Daemon"
	   		sudo service gpsd restart > /dev/null 2>&1 &
		fi
	fi
}

######################################################

start_camera()
{
	if [ "$pi_camera_method" = "pivid" ]; then
		if [ ! -z "`pgrep pivid`" ]; then
			write_log_msg "Process pivid is already running"
		else 
			write_log_msg "Starting pivid"
	  		main_dir/scripts/pivid.sh > /dev/null 2>&1 &
		fi
	elif [ "$pi_camera_method" = "picam" ]; then
		if [ ! -z "`pgrep -f picam.py`" ]; then
			write_log_msg "Process picam is already running"	
		else 
			write_log_msg "Starting picam"
			sleep 4
	  		$main_dir/scripts/picam.py > /dev/null 2>&1 &
		fi
	fi
}

######################################################

monitor_front_camera()
{
	if [ "$pi_camera_method" = "pivid" ]; then
		if [ ! -z "`pgrep pivid`" ]; then
			front_camera_status="OK"
		else 
			front_camera_status="ERROR"
			write_log_msg "ERROR - Restarting pivid"
	  		main_dir/scripts/pivid.sh > /dev/null 2>&1 &
		fi
	elif [ "$pi_camera_method" = "picam" ]; then
		if [ ! -z "`pgrep -f picam.py`" ]; then
			front_camera_status="OK"
		else 
			front_camera_status="ERROR"
			write_log_msg "ERROR - Restarting picam"
	  		$main_dir/scripts/picam.py > /dev/null 2>&1 &
		fi
	fi
}


######################################################

start_samba()
{
	if [ -f /etc/samba/smb.conf ]; then
	 if [ ! -z "`pgrep smbd`" ] || [ ! -z "`pgrep nmbd`" ]; then
	  pkill --signal SIGINT smbd ; pkill --signal SIGINT nmbd
	  sleep 1 
	 fi
	 printf "`date +%T` [ilvte-samba]: Starting nmbd and smbd\n" >> $status_out
	 nmbd -D ; smbd -D
	else
	 printf "`date +%T` [ilvte-samba]: smb.conf file not found\n" >> $status_out
	fi
}
	 
#######################################################################################

system_monitor()
{
	display_temperature="`/opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}'`"
	thermal_temperature="`cat /sys/class/thermal/thermal_zone0/temp`"
	current_speed="`cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`"
	display_speed="`expr $current_speed / 1000`Mhz"
	uptime_info="`uptime | cut -c11-80`"
	write_log_msg "FRONT SYSTEM: $uptime_info, $display_speed, $display_temperature"
	#
	#  Check disk usage
	#
	disk_usage="`df -h $main_dir | grep root | awk '{print $5}'`"
	write_log_msg "Capacity of $main_dir is $disk_usage%"

	if [ ! -z "$using_usb" ]; then
		usb_usage="`df -h $usb_directory | grep usb | awk '{print $5}'`"
		write_log_msg "Capacity of $usb_directory is $usb_usage%"
	fi

        #
        #  If temperature is over a threshold, shutdown the machine
        #
        if [ $thermal_temperature -ge $over_temp ]; then
                write_log_msg "*** Temperature critical!   Shutting down now ... ***"
                pkill --signal SIGUSR1 pwr_butt
                sleep 15
                shutdown -h -P now
                exit
        fi
}

#######################################################################################

process_monitor()
{
	monitor_gpsd
	monitor_front_camera

	write_log_msg "GPS SYSTEM STATUS    = $gpsd_status"
	write_log_msg "FRONT CAMERA STATUS  = $front_camera_status"
        write_log_msg "REAR CAMERA STATUS   = $rear_camera_status"
}

#######################################################################################
#
#   MAIN
#
#######################################################################################

trap 'time_to_die' INT TERM USR1

#
#  Read configuration parameters from global.rc file that override defaults
#
check_globals
#
#  Make directories if they do not exist
#  TODO:  Make them with permissions 777
#
mkdir -p "$main_dir/front" "$main_dir/rear" "$main_dir/audio" "$log_dir/tmp"

write_log_msg "ILVTE System (v$version) Starting up..."
write_log_msg "----------------------------------------------------------"
write_log_msg " Main Directory = $main_dir"
write_log_msg " Log Directory  = $log_dir"
write_log_msg " Log File       = $status_out"
write_log_msg " USB Mount      = $usb_mount"
write_log_msg " USB Device     = $usb_device"
write_log_msg " USB Directory  = $usb_directory"
write_log_msg "----------------------------------------------------------"

#
#  Mount USB Drive if enabled
#
check_usb

#
#  Start GPS Daemon Process
#
start_gpsd

#
#  Start Camera Recording Process
#
start_camera


#
#  Disk space status messages
#
write_log_msg "Disk space threshold is set to $root_limit%% for $main_dir"

if [ "$pivid_use_usb" = "yes" ] || [ "$motion_camera1_use_usb" = "yes" ] || [ "$audio_use_usb" = "yes" ] & [ "$storage_mounted" = "True" ]; then
	write_log_msg "Disk space threshold is set to $sub_limit%% for $main_dir/usb"
fi

#
#  Not sure why we are waiting 8 seconds before starting SAMBA
#
sleep 8
#
#  Start SAMBA
#
if [ ! -z `which smbd` ] && [ "$samba_enabled" = "yes" ]; then
	start_samba
fi

#
#  Main loop running software checks the following
#     1.  Monitors Temperature and shuts down the system if overheating
#     2.  Makes sure processes are running, and restarts them if necessary
#     3.  Monitor disk usage for recording
#
while (true)
do
	#
	#  Monitor and print out system parameters for 
	#  	Uptime
	#	Number of Users
	#	Average Load
	#	Processor Speed
	#	Temperature
	#       Disk Usage
	#
	system_monitor

	#
	#  Make sure everything is running as expected
	#
	process_monitor

	#
	#   Wait 60 seconds and check everything again
	#
	sleep 60
done
exit
