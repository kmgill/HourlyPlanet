#!/bin/bash

pushd /Users/kgill/repos/HourlyPlanet

sinceid=0

if [ -f "last_mention_id.txt" ]; then
    sinceid=`cat last_mention_id.txt`
fi

python hourlyplanet.py -r -s $sinceid -w last_mention_id.txt $@