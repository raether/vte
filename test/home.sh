#!/bin/sh
#
# (Al) - hmm.tricky@gmail.com

# need to copy final log info if possible...
# maybe add a protected dir for logs/counters if local delete is used
# maybe add date/time as an optional directory to copy to
# home_copy_method="pscp root@ip.of.box:/path/to/file ."
# or a simple copy to a SAMBA directory

  version="v0.06"

  home_local_dir="/home/camera/"
  home_copy_method="rsync"
  home_delete_local="no"
  home_delete_remote="no"

  home_remote_user="root"
  home_remote_host="127.0.0.1"
  home_remote_dir="/media/carpi/"

  status_out="/home/camera/logs/status.txt"
  rsync_options="-ua"

  global_rc="/root/scripts/global.rc"
  main_dir="/home/camera"
  usb_directory="$main_dir/usb"
  status_dir="$main_dir/logs"
  status_file="status.txt"
  status_out="$status_dir/$status_file"

  usb_device="/dev/sda1"
  usb_mount="yes"
  usb_global=""

  if [ ! -f /tmp/home.pid ]; then
   printf "$$" > /tmp/home.pid
  else
#   printf "home is already running as PID `cat /tmp/home.pid`\n"
   exit
  fi

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
	 tmp_glob="`grep usb_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then usb_directory="$tmp_glob"; fi

	 tmp_glob="`grep home_remote_user $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_remote_user="$tmp_glob"; fi
	 tmp_glob="`grep home_remote_host $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_remote_host="$tmp_glob"; fi
	 tmp_glob="`grep home_remote_dir $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_remote_dir="$tmp_glob"; fi
	 tmp_glob="`grep home_local_dir $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_local_dir="$tmp_glob"; fi
	 tmp_glob="`grep home_copy_method $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_copy_method="$tmp_glob"; fi
	 tmp_glob="`grep home_delete_local $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_delete_local="$tmp_glob"; fi
	 tmp_glob="`grep home_delete_remote $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_delete_remote="$tmp_glob"; fi
	 tmp_glob="`grep home_network_profile $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then home_network_profile="$tmp_glob"; fi
	fi
}
 	check_globals

	tmp_glob="`grep usb_device $global_rc | grep -v ^# | awk '{print$2}'`"
	if [ ! -z "$tmp_glob" ]; then usb_device="$tmp_glob"; fi
	if [ "$usb_mount" = "yes" ] && [ ! -z `mount | grep "$usb_device" | awk '{print $1}'` ]; then
	 global_rc="$usb_directory/global.rc"
	 if [ -f "$global_rc" ]; then
	  check_globals
	  usb_global="True"
	 fi
	 touch "$status_out" > /dev/null 2>&1
	 status=$?
	 if [ $status -ne 0 ]; then
	  old_status_dir="$status_dir"
          status_dir="$main_dir/logs"
	  status_out="$status_dir/$status_file"
	 fi
	fi

check_connection()
{
count=0

	if [ -n "`which netctl`" ]; then
	 netctl start $home_network_profile
	else
	 service network restart > /dev/null 2>&1
	fi

	while true
 	do
	 ping -c 4 $home_remote_host > /dev/null 2>&1
	 if [ $? -eq 1 ]; then
	  count="`expr $count + 1`"
	  if [ $count -eq 10 ]; then
	   printf "`date +%T` [home]: Giving up on $home_remote_host\n" >> $status_out
	   exit
	  fi
	  printf "`date +%T` [home]: Failed to reach $home_remote_host\n" >> $status_out
	  sleep 1
	 else
	  printf "`date +%T` [home]: $home_remote_host is reachable\n" >> $status_out
	  break
	 fi
	done
}

	check_connection
#/root/scripts/flash copy_mode &

	if [ "$home_copy_method" = "scp" ]; then
	 ls $home_local_dir |
	 while read file
	  do
	   printf "`date +%T` [home]: Copying `uname -n`:$file to $home_remote_host:$home_remote_dir\n" >> $status_out
	   scp -rpq $home_local_dir/"$file" $home_remote_user@$home_remote_host:$home_remote_dir/
	  done
	 printf "`date +%T` [home]: File copy completed\n" >> $status_out
	else
	 if [ "$home_delete_local" = "yes" ]; then
	  rsync_options="$rsync_options --remove-source-files"
	  if [ -n "$usb_global" ]; then cp $global_rc /var/tmp/; fi
	 fi
	 if [ "$home_delete_remote" = "yes" ]; then
	  rsync_options="$rsync_options --delete"
	 fi
	 printf "`date +%T` [home]: Syncing from `uname -n`:$home_local_dir to $home_remote_host:$home_remote_dir\n" >> $status_out
	 rsync $rsync_options --out-format='	 [home]: Sync %n' $home_local_dir $home_remote_user@$home_remote_host:$home_remote_dir >> $status_out

	 if [ $? -ne 0 ]; then printf "`date +%T` [home]: $home_copy_method did not complete successfully\n" >> $status_out;
	 else printf "`date +%T` [home]: $home_copy_method completed successfully\n" >> $status_out; fi

	 if [ "$home_delete_local" = "yes" ]; then
	  if [ -n "$usb_global" ]; then cp /var/tmp/global.rc $global_rc; fi
	 fi

	fi
	rm -f /tmp/home.pid
exit
