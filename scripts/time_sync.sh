
control_time=`date`
left_time=`ssh left.local date`
front_time=`ssh front.local date`
rear_time=`ssh rear.local date`

echo "GPS Status:"
sudo service gpsd status | head -6

echo ""
echo "Estimated Time:"
echo "Control Time : ${control_time}"
echo "Front Time   : ${front_time}"
echo "Left Time    : ${left_time}"
echo "Rear Time    : ${rear_time}"
echo ""
echo "Accuracy wihtin 1-2 seconds of each other means clocks are synced"
echo ""
echo "Chrony Time Source Information - * means tune source is synced"
echo "control.local"
chronyc sources
echo ""
echo "left.local"
ssh left.local "chronyc sources"
echo ""
echo "front.local"
ssh front.local "chronyc sources"
echo ""
echo "rear.local"
ssh rear.local "chronyc sources"
