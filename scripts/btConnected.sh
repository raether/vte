#!/bin/bash

/home/camera/vte/scripts/btInfo.sh | grep "Connected" | awk '{print $2}'
