# HourlyPlanet

Hourlyplanet is a Python script which backs the Hourlycosmos Twitter account. It picks random images from the configured Flickr users photostreams or albums and tweets it with the description, name, Twitter @, and a shortened link to the source. The script will either do a direct post (`-p` option) or respond to Twitter mentions (`-r` option). Twitter mentions are checked if they contain the text 'please' and will respond if it detects it. 

```
usage: hourlyplanet.py [-h] [-c CONFIG] [-r] [-p] [-s SINCEID] [-w WRITEIDTO]
                       [-S SOURCES]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Specify an alternate configuration file
  -r, --respond         Respond to Twitter mentions
  -p, --post            Post as status update
  -s SINCEID, --sinceid SINCEID
                        Most recent known mention id
  -w WRITEIDTO, --writeidto WRITEIDTO
                        Write most recent mention id to file
  -S SOURCES, --sources SOURCES
                        Specify an alternate sources yaml file

```
