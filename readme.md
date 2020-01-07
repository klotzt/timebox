# Timebox Project
##  Overview
This repo contains file to operate the race timing software.
It is supposed to run on a raspbery pi (zero) and connect to Wiegand RF-ID reads that read the tags from runners/swimmers.
It produces a CSV file as an output with the BIB-Numbers and time (time of day) to be post-processed by race-timing software 
In addition it serves as a server to the Raceresult software (see https://www.raceresult.com/de-de/home/index.php)
## Components
- timboxd
Daemon file to autotstart the scripts upon boot
Copy to /etc/init.d and change mode to executable
- Makefile+wiegand_rpi.c
Sourcefile for interfacing with wiegand RFID readers
- timebox.py
Python script to get it all together

## Building wiegand interface
- just call make in this dir
- make sure you have wiring pi library installed first (default installed on raspbian): http://wiringpi.com/ or https://github.com/WiringPi/WiringPi



