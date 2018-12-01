LOGDIR="/home/camera/vte/logs/"
PROCESSFILE=$LOGDIR/timeProcess.txt
TIMEFILE=$LOGDIR/currentTimes.txt
CHRONYFILE=$LOGDIR/chronyTime.txt
RPTFILE=$LOGDIR/time_report.txt

echo "GPS Status:" > $PROCESSFILE
sudo service gpsd status | head -3 >> $PROCESSFILE
echo "" >> $PROCESSFILE
sudo service chronyd status | head -3 >> $PROCESSFILE
echo "" >> $PROCESSFILE

left_time=`ssh left.local date &`
front_time=`ssh front.local date &`
rear_time=`ssh rear.local date &`
control_time=`date &`
sleep 1

echo "Estimated Time:" > $TIMEFILE
echo "------------------------------" >> $TIMEFILE
echo "Control Time : ${control_time}" >> $TIMEFILE
echo "Front Time   : ${front_time}" >> $TIMEFILE
echo "Left Time    : ${left_time}" >> $TIMEFILE
echo "Rear Time    : ${rear_time}" >> $TIMEFILE
echo "" >> $TIMEFILE

echo "Accuracy wihtin 1-2 seconds of each other means clocks are synced" >> $TIMEFILE
echo "Chrony Time Source Information - * means time source is synced" > $CHRONYFILE
echo "" >> $CHRONYFILE
echo "control.local" >> $CHRONYFILE
chronyc sources >> $CHRONYFILE
echo "" >> $CHRONYFILE
echo "left.local" >> $CHRONYFILE
ssh left.local "chronyc sources" >> $CHRONYFILE
echo "" >> $CHRONYFILE
echo "front.local" >> $CHRONYFILE
ssh front.local "chronyc sources" >> $CHRONYFILE
echo "" >> $CHRONYFILE
echo "rear.local" >> $CHRONYFILE
ssh rear.local "chronyc sources" >> $CHRONYFILE

cat $PROCESSFILE $TIMEFILE $CHRONYFILE > $RPTFILE
