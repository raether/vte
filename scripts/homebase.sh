#!/bin/sh
# 
#  Video Traffice Enforcement
#  Home Base Script
#

#
#  Set defaults for variables
#
  global_rc="/home/camera/vte/scripts/global.rc"
  main_dir="/home/camera/vte"
  log_dir="$main_dir/logs"
  data_dir="$main_dir/data"
  log_file="status.log"
  status_out="$log_dir/$log_file"

  front_hostname="front.local"
  rear_hostname="rear.local"
  left_hostname="left.local"

  home_remote_host="vault.local"
  home_remote_user="car101"
  home_remote_dir="car101"

  rsync_options="-av"

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

write_log_msg()
{
	printf "`date +%T` [HOMEBASE]: $1\n" >> $status_out
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

prepare_host()
{
	write_log_msg "Preparing $home_remote_host for file synchronization"
	ssh $home_remote_user@$home_remote_host mkdir -p "logs" 
	ssh $home_remote_user@$home_remote_host mkdir -p "data" 
	ssh $home_remote_user@$home_remote_host mkdir -p "data/front" 
	ssh $home_remote_user@$home_remote_host mkdir -p "data/rear" 
	ssh $home_remote_user@$home_remote_host mkdir -p "data/left" 
	ssh $home_remote_user@$home_remote_host mkdir -p "data/gps" 
	ssh $home_remote_user@$home_remote_host mkdir -p "data/radar" 
}
######################################################

rsync_front()
{
	write_log_msg "Start Synchronization Files from $front_hostname"
	rsync --remove-source-files --partial --progress -av "$data_dir/front/" "$home_remote_user@$home_remote_host:data/front"
	rsync --remove-source-files --partial -av "$data_dir/gps/" "$home_remote_user@$home_remote_host:data/gps"
	rsync --remove-source-files --partial -av "$data_dir/radar/" "$home_remote_user@$home_remote_host:data/radar"
	write_log_msg "Finish Synchronization Files from $front_hostname"
}

######################################################

rsync_rear()
{
	write_log_msg "Start Synchronization Files from $rear_hostname"
	ssh $rear_hostname rsync --remove-source-files --partial -av "$data_dir/rear/" "$home_remote_user@$home_remote_host:data/rear"
	write_log_msg "Finish Synchronization Files from $rear_hostname"
}


######################################################

rsync_left()
{
	write_log_msg "Start Synchronization Files from $left_hostname"
	ssh $left_hostname rsync --remove-source-files --partial -av "$data_dir/left/" "$home_remote_user@$home_remote_host:data/left"
	write_log_msg "Finish Synchronization Files from $left_hostname"
}


######################################################

rsync_files()
(
	prepare_host
	rsync_front &
        rsync_rear &
	rsync_left &
	#
	#  Make sure they finish before we exit function
	#
	wait
	write_log_msg "Finished System Synchronization"
)


#######################################################################################
#
#   MAIN
#
#######################################################################################


while (true)
do
	#
	#  ping homebase host to see if it is connected.
	#
        ping -c 4 $home_remote_host

        if [ $? -eq 0 ]; then
             write_log_msg "$home_remote_host reachable - start file synchronization"
             #
             #  Rsync Files to remote host
             #
             rsync_files
        else
             write_log_msg "$home_remote_host NOT reachable"
        fi

	#
	#   Wait 60 seconds and check everything again
	#
	sleep 60
done
exit
