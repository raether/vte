#! /bin/bash

if ! pactl list sinks short | grep bluez >/dev/null;
then
    echo bluez sink not found, attempting to disconnect-reconnect;
    bluetoothctl <<EOF
connect 88:C6:26:ED:44:D8
quit
EOF

    sleep 5
    bt_source_index=`pactl list sources short | grep bluez_source | cut -f1`
    bt_source=`pactl list sources short | grep bluez_source | cut -f2`
    bt_sink_index=`pactl list sinks short | grep bluez_sink | cut -f1`
    bt_sink=`pactl list sinks short | grep bluez_sink | cut -f2`

    echo "Connecting source to $bt_source"
    echo "Connecting sink to $bt_sink"

    pactl set-default-source $bt_source
    pactl set-default-sink $bt_sink
    pactl set-sink-volume $bt_sink_index 32000
  
else
    echo "bluez sink found"
fi
