#!/bin/bash

pushd /home/pi/repos/HourlyPlanet
python3 hourlyplanet.py -p -d twitter >> run.log 2>&1 
