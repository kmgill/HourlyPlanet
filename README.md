# HourlyPlanet

Hourlyplanet is a Python script which backs the Hourlycosmos Twitter account. It picks random images from the configured Flickr users photostreams or albums and tweets it with the description, name, Twitter @, and a shortened link to the source. The script will either do a direct post (`-p` option) or respond to Twitter mentions (`-r` option). Twitter mentions are checked if they contain the text 'please' and will respond if it detects it. 

## Program Options
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
## Program Configuration
Program configuration is contained in the `config.ini` file.

Example:

```ini
[flickr]
flickr.key=<Flickr API Key>
flickr.secret=<Flickr API Secret>
flickr.page_size=100
flickr.image_url_attribute=url_z

[twitter]
twitter.consumer_key=<Twitter Consumer Key>
twitter.consumer_secret=<Twitter Consumer Secret>
twitter.access_token=<Twitter Access Token>
twitter.access_secret=<Twitter Access Secret>

```

## Sources Configuration
The `sources.yaml` file specifies the Flickr accounts used as sources for the program. For each source, it contains the person's Flickr ID in numeric form, their Twitter account name (@screenname), and optionally an array of album ids if not using the users photostream. You may also set a source as disabled if you need to temporarily pause pulling from that account.

Example:
```yaml
sources:
  -
    flickr_id: '123456789@N05'
    twitter_id: '@TwitterPerson1'
    albums:
      - 72157712420147562
      - 72151947259511817
  -
    flickr_id: '987654321@N03'
    twitter_id: '@TwitterPerson2'
  -
    flickr_id: '987659876@N03'
    twitter_id: '@TwitterPerson3'
    disabled: true
```

## Responding to Mentions
For the program to respond to only those mentions that have posted since it was last run, it must know the id of the last mention that was seen. This is passed in using the `-s <id>` option. To have the program write the most recent id during a particular run to a file use the `-w filename` option at runtime. If running as a cronjob, an example wrapper bash script is as follows:

```bash
#!/bin/bash

pushd /Users/kgill/repos/HourlyPlanet

sinceid=0

if [ -f "last_mention_id.txt" ]; then
    sinceid=`cat last_mention_id.txt`
fi

python hourlyplanet.py -r -s $sinceid -w last_mention_id.txt $@
```

