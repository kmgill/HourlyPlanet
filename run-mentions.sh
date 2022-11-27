#!/bin/bash

pushd /home/pi/repos/HourlyPlanet

sinceid=0

if [ -f "last_mention_id.txt" ]; then
    sinceid=`cat last_mention_id.txt`
fi

python hourlyplanet.py -r -s $sinceid -w last_mention_id.txt -d twitter $@ >> run.log 2>&1
