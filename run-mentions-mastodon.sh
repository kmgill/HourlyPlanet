#!/bin/bash

pushd /home/pi/repos/HourlyPlanet

sinceid=0

if [ -f "last_mention_id_mstdn.txt" ]; then
    sinceid=`cat last_mention_id_mstdn.txt`
fi

python hourlyplanet.py -r -s $sinceid -w last_mention_id_mstdn.txt -d mastodon $@ >> run_mastodon.log 2>&1