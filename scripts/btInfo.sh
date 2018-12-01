#!/bin/bash

MAC_ADDRESS="88:C6:26:ED:44:D8"

(
  echo 'info 88:C6:26:ED:44:D8'
  echo quit
) | bluetoothctl
