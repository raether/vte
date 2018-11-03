#!/bin/sh
# 
#  Video Traffice Enforcement
#

#
# VTE stop all processes
#

ssh camera@left.local pkill --signal SIGTERM -f camera.py
ssh camera@rear.local pkill --signal SIGTERM -f camera.py
ssh camera@front.local pkill --signal SIGTERM -f camera.py
pkill --signal SIGTERM -f audio.py
pkill --signal SIGTERM -f rear_view_camera.sh
pkill --signal SIGTERM -f navit 
pkill --signal SIGTERM -f radar.py
pkill --signal SIGTERM -f gps_logger.py
