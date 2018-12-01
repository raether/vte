echo "Bringing Down Wifi Interfaces"
ssh left.local "sudo ifconfig wlan0 down" &
ssh front.local "sudo ifconfig wlan0 down" &
ssh rear.local "sudo ifconfig wlan0 down" &
sudo ifconfig wlan0 down
sudo systemctl restart avahi-daemon
sleep 1
ping -c 1 left.local
ping -c 1 front.local
ping -c 1 rear.local
