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

        write_log_msg "Stopping Left Video Camera"
	pkill --signal SIGTERM -f camera.py
	sleep 1

        write_log_msg "Stopping Rear Video Camera"
	ssh camera@rear.local pkill --signal SIGTERM -f camera.py
	sleep 1

        write_log_msg "Stopping Front Video Camera"
	ssh camera@front.local pkill --signal SIGTERM -f camera.py
	sleep 1

        write_log_msg "Stopping Rear View"
	pkill --signal SIGTERM -f rear_view_camera.sh
	sleep 1

        write_log_msg "Stopping Navigation System"
	pkill --signal SIGTERM -f navit 
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

start_logview()
{
    nohup xterm -geometry 150x36+980+16 -fn "-adobe-courier-medium-r-normal--14-100-100-100-m-90-iso10646-1" -e "tail -f $status_out" > /dev/null 2>&1 &
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

sync_time()
{
	write_log_msg "Sync Front Processor Time"
	$main_dir/scripts/gpstime.py
	write_log_msg "Sync Rear Processor Time"
        ssh camera@rear.local $main_dir/scripts/gpstime.py
	write_log_msg "Sync Front Processor Time"
        ssh camera@front.local $main_dir/scripts/gpstime.py
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

start_left_camera()
{
	if [ ! -z "`pgrep -f camera.py`" ]; then
		write_log_msg "Left Video Camera Process is already running"	
	else 
		write_log_msg "Starting Left Video Camera"
  		$main_dir/scripts/camera.py --view left --hflip --display ur > /dev/null 2>&1 &
	fi
}

######################################################

monitor_left_camera()
{
	if [ ! -z "`pgrep -f camera.py`" ]; then
		left_camera_status="OK"
	else 
		left_camera_status="ERROR"
		write_log_msg "ERROR - Restarting Left Video Camera Process"
  		$main_dir/scripts/camera.py --view left --hflip --display ur > /dev/null 2>&1 &
	fi
}

######################################################

start_rear_camera()
{
	if [ ! -z "`ssh rear.local pgrep -f camera.py`" ]; then
		write_log_msg "Rear Video Camera Process is already running"	
	else 
		write_log_msg "Starting Rear Video Camera"
  		ssh rear.local $main_dir/scripts/camera.py --view rear --display full --stream > /dev/null 2>&1 &
	fi
}

######################################################

monitor_rear_camera()
{
	if [ ! -z "`ssh rear.local pgrep -f camera.py`" ]; then
		rear_camera_status="OK"
	else 
		rear_camera_status="ERROR"
		write_log_msg "ERROR - Restarting Rear Video Camera Process"
  		ssh rear.local $main_dir/scripts/camera.py --view rear --display full --stream > /dev/null 2>&1 &
	fi
}

######################################################

start_front_camera()
{
	if [ ! -z "`ssh front.local pgrep -f camera.py`" ]; then
		write_log_msg "Front Video Camera Process is already running"	
	else 
		write_log_msg "Starting Front Video Camera"
  		ssh front.local $main_dir/scripts/camera.py --view front --display full --stream > /dev/null 2>&1 &
	fi
}

######################################################

monitor_front_camera()
{
	if [ ! -z "`ssh front.local pgrep -f camera.py`" ]; then
		front_camera_status="OK"
	else 
		front_camera_status="ERROR"
		write_log_msg "ERROR - Restarting Front Video Camera Process"
  		ssh front.local $main_dir/scripts/camera.py --view front --display full --stream > /dev/null 2>&1 &
	fi
}

######################################################

start_frontview()
{
	if [ ! -z "`pgrep -f front_view_camera.sh`" ]; then
		write_log_msg "Front View is already running"	
	else 
		write_log_msg "Starting Front View "
  		$main_dir/scripts/front_view_camera.sh &
	fi
}

######################################################

monitor_frontview()
{
	if [ ! -z "`pgrep -f front_view_camera.sh`" ]; then
		frontview_status="OK"
	else 
		frontview_status="ERROR"
		write_log_msg "ERROR - Restarting Front View Process"
  		$main_dir/scripts/front_view_camera.sh &
	fi
}

######################################################


######################################################

start_rearview()
{
	if [ ! -z "`pgrep -f rear_view_camera.sh`" ]; then
		write_log_msg "Rear View is already running"	
	else 
		write_log_msg "Starting Rear View "
  		$main_dir/scripts/rear_view_camera.sh &
	fi
}

######################################################

monitor_rearview()
{
	if [ ! -z "`pgrep -f rear_view_camera.sh`" ]; then
		rearview_status="OK"
	else 
		rearview_status="ERROR"
		write_log_msg "ERROR - Restarting Rear View Process"
  		$main_dir/scripts/rear_view_camera.sh &
	fi
}

######################################################

start_homebase()
{
	if [ ! -z "`pgrep -f homebase`" ]; then
		write_log_msg "Home Base is already running"	
	else 
		write_log_msg "Starting Home Base"
  		$main_dir/scripts/homebase.sh > /dev/null 2>&1 &
	fi
}

######################################################

monitor_homebase()
{
	if [ ! -z "`pgrep -f homebase`" ]; then
		homebase_status="OK"
	else 
		homebase_status="ERROR"
		write_log_msg "ERROR - Restarting Home Base"
                $main_dir/scripts/homebase.sh > /dev/null 2>&1 &
	fi
}

######################################################

start_navit()
{
	if [ ! -z "`pgrep -f navit`" ]; then
		write_log_msg "Navigation System is already running"	
	else 
		write_log_msg "Starting Navigation System"
  		navit > /dev/null 2>&1 &
	fi
}

######################################################

monitor_navit()
{
	if [ ! -z "`pgrep -f navit`" ]; then
		navit_status="OK"
	else 
		navit_status="ERROR"
		write_log_msg "ERROR - Restarting Navigation System"
  		navit  > /dev/null 2>&1 &
	fi
}

######################################################

system_monitor()
{
	left_display_temperature="`/opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}'`"
	left_thermal_temperature="`cat /sys/class/thermal/thermal_zone0/temp`"
	left_current_speed="`cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`"
	left_display_speed="`expr $left_current_speed / 1000`Mhz"
	left_uptime_info="`uptime | cut -c11-80`"
	left_disk_usage="`df -h $main_dir | grep root | awk '{print $5}'`"

	rear_display_temperature="`ssh rear.local /opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}'`"
	rear_thermal_temperature="`ssh rear.local cat /sys/class/thermal/thermal_zone0/temp`"
	rear_current_speed="`ssh rear.local cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`"
	rear_display_speed="`expr $rear_current_speed / 1000`Mhz"
	rear_uptime_info="`ssh rear.local uptime | cut -c11-80`"
	rear_disk_usage="`ssh rear.local df -h $main_dir | grep root | awk '{print $5}'`"

	front_display_temperature="`ssh front.local /opt/vc/bin/vcgencmd measure_temp | awk -F\= '{print $2}'`"
	front_thermal_temperature="`ssh front.local cat /sys/class/thermal/thermal_zone0/temp`"
	front_current_speed="`ssh front.local cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`"
	front_display_speed="`expr $front_current_speed / 1000`Mhz"
	front_uptime_info="`ssh front.local uptime | cut -c11-80`"
	front_disk_usage="`ssh front.local df -h $main_dir | grep root | awk '{print $5}'`"

	write_log_msg "FRONT SYSTEM: $front_uptime_info, $front_display_speed, $front_display_temperature"
	write_log_msg "REAR SYSTEM: $rear_uptime_info, $rear_display_speed, $rear_display_temperature"
	write_log_msg "LEFT SYSTEM: $left_uptime_info, $left_display_speed, $left_display_temperature"

	write_log_msg "FRONT SYSTEM: Disk Usage is $front_disk_usage%"
	write_log_msg "REAR SYSTEM : Disk Usage is $rear_disk_usage%"
	write_log_msg "LEFT SYSTEM : Disk Usage is $left_disk_usage%"

        #
        #  If temperature is over a threshold, shutdown the machine
        #
        if [ $left_thermal_temperature -ge $over_temp ]; then
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
        monitor_rear_camera
        monitor_left_camera
        monitor_frontview
        monitor_rearview
        monitor_navit
        monitor_homebase

	write_log_msg "FRONT CAMERA STATUS  = $front_camera_status"
        write_log_msg "REAR CAMERA STATUS   = $rear_camera_status"
        write_log_msg "LEFT CAMERA STATUS   = $left_camera_status"
        write_log_msg "FRONT VIEW STATUS    = $frontview_status"
        write_log_msg "REAR VIEW STATUS     = $rearview_status"
	write_log_msg "GPS SYSTEM STATUS    = $gpsd_status"
        write_log_msg "RADAR SYSTEM STATUS  = $radar_status"
        write_log_msg "NAVIGATION STATUS    = $navit_status"
        write_log_msg "HOMEBASE STATUS      = $homebase_status"
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
#
#  Start Log Viewer
#
# start_logview
# sleep 2

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
#  Synchronize Time Across Servers
#
sync_time
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
start_left_camera
start_front_camera
start_rear_camera
#
#  Turn on rear view camera viewer
#
sleep 5
start_frontview
start_rearview
#
#  Start Navit Navigation Maps
#
start_navit
#
#  Start Home Base Automatic File Upload
#
# start_homebase
#
#  Disk space status messages
#
write_log_msg "Disk space threshold is set to $root_limit%% for $main_dir"

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
