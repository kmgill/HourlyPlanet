#!/bin/bash

pushd /home/pi/repos/HourlyPlanet
python hourlyplanet.py -p -d mastodon >> run_mastodon.log 2>&1 
