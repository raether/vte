#/bin/bash

echo -e "paired-devices \nquit" | bluetoothctl | grep "^Device" | grep "88:C6:26:ED:44:D8"

