#!/bin/sh
#
# (Al) - hmm.tricky@gmail.com

  version="v2-1.94"

  global_rc="/root/scripts/global.rc"
  main_dir="/home/camera"
  usb_directory="$main_dir/usb"
  log_dir="$main_dir/logs"
  status_file="status.txt"
  status_out="$log_dir/$status_file"

  audio_enabled="no"
  audio_device="plughw:1,0"
  audio_length="720"
  audio_options="-c 2 -r 16000 -f S16_LE"

  usb_device="/dev/sda1"
  usb_mount="yes"

  GPS_wait="yes"

printf "$$" > /tmp/audio.pid

stop_audio()
{
	pkill --signal SIGINT arecord
	if [ "$ep_date" != "TRUE" ]; then
	 printf "`date +%T` [audio]: Stopped audio at `date +%Y%m%d%H%M%S` (Event $file_count - $sequence_count files)\n" >> $status_out
	else
	 printf "`date +%T` [audio]: Stopped audio recording $date_time (Event $file_count - $sequence_count files)\n" >> $status_out
	fi
	printf "audio closed\0" >> /tmp/dash_fifo &
	sync
	exit
}
	trap 'stop_audio' INT TERM USR1

check_globals()
{
	if [ -f $global_rc ]; then
	 tmp_glob="`grep main_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then main_dir="$tmp_glob"; fi
	 tmp_glob="`grep log_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then
	  log_dir="$tmp_glob"
	  status_out="$log_dir/$status_file"
	 fi
	 tmp_glob="`grep audio_enabled $global_rc | grep -v ^# | awk '{print$2}'`"
  	 if [ ! -z "$tmp_glob" ]; then audio_enabled="$tmp_glob"; fi
	 tmp_glob="`grep audio_device $global_rc | grep -v ^# | awk '{print$2}'`"
  	 if [ ! -z "$tmp_glob" ]; then audio_device="$tmp_glob"; fi
	 tmp_glob="`grep audio_length $global_rc | grep -v ^# | awk '{print$2}'`"
  	 if [ ! -z "$tmp_glob" ]; then audio_length="$tmp_glob"; fi
	 tmp_glob="`grep audio_options $global_rc | grep -v ^# | cut -c 16-80`"
  	 if [ ! -z "$tmp_glob" ]; then audio_options="$tmp_glob"; fi
	 tmp_glob="`grep audio_use_usb $global_rc | grep -v ^# | awk '{print$2}'`"
  	 if [ ! -z "$tmp_glob" ]; then audio_use_usb="$tmp_glob"; fi
	 tmp_glob="`grep GPS_wait $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then GPS_wait="$tmp_glob"; fi

	 tmp_glob="`grep usb_mount $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then usb_mount="$tmp_glob"; fi
	 tmp_glob="`grep usb_directory $global_rc | grep -v ^# | awk '{print$2}'`"
	 if [ ! -z "$tmp_glob" ]; then usb_directory="$tmp_glob"; fi
	fi
}
	check_globals
	mkdir -p "$main_dir/front" "$main_dir/rear" "$main_dir/audio" "$log_dir/tmp"

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
	  old_log_dir="$log_dir"
	  log_dir="$main_dir/logs"
	  status_out="$log_dir/$status_file"
	  printf "`date +%T` [audio]: * Write failed for $old_log_dir on $usb_device. Using $log_dir *\n" >> $status_out
	 fi

	 if [ "$audio_use_usb" = "yes" ]; then
	  touch "$usb_directory/.test" > /dev/null 2>&1
	  status=$?
	  if [ $status -ne 0 ]; then
	   printf "`date +%T` [audio]: * Write failed for $usb_directory/audio on $usb_device. Using $main_dir/audio *\n" >> $status_out
#	   umount $usb_device > /dev/null 2>&1
	  else
	   main_dir="$usb_directory"
	   mkdir -p "$main_dir/front" "$main_dir/rear" "$main_dir/audio" "$main_dir/logs/tmp"
	  fi
	 fi
	else
	 if [ "$audio_use_usb" = "yes" ]; then
	  printf "`date +%T` [audio]: Notice: \"audio_use_usb\" is $audio_use_usb, \"usb_mount\" is $usb_mount\n" >> $status_out
	 fi
	fi

	if [ "$audio_enabled" = "no" ]; then
	 printf "`date +%T` [audio]: audio is disabled in $global_rc. Exiting.\n" >> $status_out
printf "audio closed\0" >> /tmp/dash_fifo &
	 exit
	fi

	if [ `date +%Y` -eq "1970" ]; then ep_date=TRUE;
	else ep_date=FALSE; fi

	sequence_count=1

	if [ ! -f $log_dir/tmp/event.ct ]; then
	 printf "`date +%T` [audio]: Creating event counter.\n" >> $status_out
	 printf "0" > $log_dir/tmp/event.ct
	fi
	if [ ! -f $log_dir/tmp/audio.ct ]; then
	 printf "`date +%T` [audio]: Creating audio counter.\n" >> $status_out
	 printf "0" > $log_dir/tmp/audio.ct
	fi

	event_count="`cat $log_dir/tmp/event.ct`"
	file_count="`cat $log_dir/tmp/audio.ct`"
	if [ -f /tmp/first_run.tmp ]; then
	 if [ $file_count -eq $event_count ]; then
	  file_count="`expr $file_count + 1`"
	  printf "$file_count" > $log_dir/tmp/event.ct
	 else
	  file_count="`cat $log_dir/tmp/event.ct`"
	 fi
	 printf "$file_count" > $log_dir/tmp/audio.ct
	else
	 event_count="`expr $event_count + 1`"
	 printf "$event_count" > $log_dir/tmp/event.ct
	 touch /tmp/first_run.tmp
	 printf "$event_count" > $log_dir/tmp/audio.ct
	 file_count=$event_count
	fi
	if [ $file_count -lt 10 ];then file_count="0$file_count"; fi

	gps_count=0
	if [ "$GPS_wait" = "yes" ] && [ ! -z `pgrep gps_logger` ]; then
	 while [ ! -f /tmp/gps_fix.tmp ]
	  do
	   sleep 1
	   gps_count="`expr $gps_count + 1`"
	   if [ $gps_count -ge 180 ]; then
            printf "`date +%T` [audio]: Timed out waiting for GPS\n" >> $status_out
	    break
	   fi
	  done
	fi

	while(true)
	 do
	  dev_count="`arecord -l | wc -l`"
	  if [ $dev_count -le 1 ]; then
	   printf "`date +%T` [audio]: No audio device found ($dev_count).\n" >> $status_out
	   sleep 60
	  else break
	  fi
	 done

	 while(true)
	  do
	   if [ "$ep_date" = "FALSE" ]; then
	    date_time="`date +%Y%m%d%H%M`"
	   else
	    date_time="audio"
	   fi

	   if [ $sequence_count -lt 10 ];then sequence_count="0$sequence_count"; fi

	   printf "`date +%T` [audio]: Started audio recording $main_dir/audio/$file_count-$sequence_count_$date_time\n" >> $status_out

#audio_options="-f cd"
#audio_options="-c 2 -r 32000 / 22050 / 16000 -f S16_LE"

#	   /usr/bin/arecord -d $audio_length -D $audio_device $audio_options $main_dir/audio/$file_count-$sequence_count_$date_time.wav > /dev/null 2>&1
	   /usr/bin/arecord -d $audio_length -D $audio_device $audio_options $main_dir/audio/$file_count-$sequence_count_$date_time.wav > /dev/null 2>&1
	   sequence_count="`expr $sequence_count + 1`"
	  done
