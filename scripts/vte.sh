#!/bin/sh
# 
#  Video Traffice Enforcement
#

#
# VTE start up program
#

  version="0.1"

#
#  Set defaults for variables
#
  global_rc="/home/camera/vte/scripts/global.rc"
  main_dir="/home/camera/vte"
  log_dir="$main_dir/logs"
  data_dir="$main_dir/data"
  log_file="status.log"
  status_out="$log_dir/$log_file"

  front_host_name="front.local"
  back_host_name="back.local"
  left_host_name="left.local"

  GPS_enabled="yes"
  GPS_wait="yes"
  RADAR_enabled="yes"
  audio_enabled="no"
  pico_enabled="no"

  high_temp="81000"
  low_temp="77000"
  over_temp="84000"

  root_limit=95
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
#  Kill all processes associated with VTE 
#
	write_log_msg "Stopping..."
        write_log_msg "Stopping Video Camera"
	pkill --signal SIGTERM -f camera.py
	sleep 1
        write_log_msg "Stopping Radar"
	pkill --signal SIGTERM -f radar.py
	sleep 1
        write_log_msg "Stopping GPS Logger"
	pkill --signal SIGTERM -f gps_logger.py
	sleep 1

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

write_log_msg()
{
	printf "`date +%T` [VTE]: $1\n" >> $status_out
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

start_gps()
{
	if [ "$GPS_enabled" = "yes" ]; then
		if [ ! -z "`pgrep gps_logger`" ]; then
			write_log_msg "GPS Logger is already running"
		else 
			write_log_msg "Starting GPS Logger"
                        $main_dir/scripts/gps_logger.py > /dev/null 2>&1 &
		fi
	fi
}

######################################################

monitor_gps()
{
	if [ "$GPS_enabled" = "yes" ]; then
		if [ ! -z "`pgrep gps_logger`" ]; then
			gps_status="OK"
		else 
			gps_status="ERROR"
			write_log_msg "ERROR:  Restarting GPS Logger"
	   		$main_dir/scripts/gps_logger.py > /dev/null 2>&1 &
		fi
	fi
}

######################################################

start_radar()
{
        if [ "$RADAR_enabled" = "yes" ]; then
                if [ ! -z "`pgrep radar`" ]; then
                        write_log_msg "Radar is already running"
                else
                        write_log_msg "Starting Radar"
                        $main_dir/scripts/radar.py > /dev/null 2>&1 &
                fi
        fi
}

######################################################

monitor_radar()
{
        if [ "$RADAR_enabled" = "yes" ]; then
                if [ ! -z "`pgrep radar`" ]; then
                        radar_status="OK"
                else
                        radar_status="ERROR"
                        write_log_msg "ERROR:  Restarting Radar"
                        $main_dir/scripts/radar.py > /dev/null 2>&1 &
                fi
        fi
}

######################################################


start_camera()
{
	if [ ! -z "`pgrep -f camera.py`" ]; then
		write_log_msg "Video Camera Process is already running"	
	else 
		write_log_msg "Starting video camera"
		sleep 4
  		$main_dir/scripts/camera.py > /dev/null 2>&1 &
	fi
}

######################################################

monitor_front_camera()
{
	if [ ! -z "`pgrep -f camera.py`" ]; then
		front_camera_status="OK"
	else 
		front_camera_status="ERROR"
		write_log_msg "ERROR - Restarting picam"
  		$main_dir/scripts/camera.py > /dev/null 2>&1 &
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
        monitor_gps
        monitor_radar
	monitor_front_camera

	write_log_msg "FRONT CAMERA STATUS  = $front_camera_status"
        write_log_msg "REAR CAMERA STATUS   = $rear_camera_status"
        write_log_msg "LEFT CAMERA STATUS   = $left_camera_status"
	write_log_msg "GPS SYSTEM STATUS    = $gpsd_status"
        write_log_msg "RADAR SYSTEM STATUS  = $radar_status"
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
mkdir -p "$data_dir/front" 
mkdir -p "$data_dir/rear" 
mkdir -p "$data_dir/left" 
mkdir -p "$data_dir/radar" 
mkdir -p "$data_dir/gps" 
mkdir -p "$data_dir/audio"
mkdir -p "$log_dir"

write_log_msg "Video Traffic Enforcement System (v$version) Starting up..."
write_log_msg "----------------------------------------------------------"
write_log_msg " Main Directory = $main_dir"
write_log_msg " Log Directory  = $log_dir"
write_log_msg " Log File       = $status_out"
write_log_msg " Data Directory = $data_dir"
write_log_msg "----------------------------------------------------------"

#
#  Start GPS Daemon Process
#
start_gpsd
#
#  Start GPS Logger
#
start_gps
#
#  Start Radar Logger
#
start_radar

#
#  Start Camera Recording Process
#
start_camera

#
#  Disk space status messages
#
write_log_msg "Disk space threshold is set to $root_limit%% for $main_dir"

#
#  Not sure why we are waiting 8 seconds before starting SAMBA
#
sleep 5
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
