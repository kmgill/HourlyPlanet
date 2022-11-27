#!/bin/bash

pushd /home/pi/repos/HourlyPlanet
python hourlyplanet.py -p -d twitter >> run.log 2>&1 
