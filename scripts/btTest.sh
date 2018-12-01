#!/bin/bash

MAC_ADDRESS="88:C6:26:ED:44:D8"
echo "Connecting to ${MAC_ADDRESS}"

(
  sleep 1
  echo 'info 88:C6:26:ED:44:D8'
  sleep 1
  echo quit
) | bluetoothctl
