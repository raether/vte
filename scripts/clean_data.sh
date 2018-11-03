#!/bin/bash

rm -r /home/camera/vte/data/gps/*
rm -r /home/camera/vte/data/audio/*
rm -r /home/camera/vte/data/radar/*
rm -r /home/camera/vte/logs/*
ssh left.local "rm -r /home/camera/vte/logs/*"
ssh left.local "rm -r /home/camera/vte/data/left/*"
ssh front.local "rm -r /home/camera/vte/logs/*"
ssh front.local "rm -r /home/camera/vte/data/front/*"
ssh rear.local "rm -r /home/camera/vte/logs/*"
ssh rear.local "rm -r /home/camera/vte/data/rear/*"
