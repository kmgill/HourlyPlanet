"""
Copyright 2021 Kevin M. Gill
Twitter: @kevinmgill
Instagram: @apoapsys
Flickr: https://www.flickr.com/photos/kevinmgill/

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import os
import requests
from configparser import ConfigParser
import math
import traceback
import json
import argparse
import re
import yaml
from yaml import CLoader as Loader

from util import Util
from flickr import Flickr, NoAlbumsFoundException, NoPhotosFoundException
from twitter import Twitter
from mstdn import MastodonClient
from source import Source


def find_and_post_image(config, sources, flickr, twitter, search_term=None, respond_to_user=None, respond_to_id=None):

    source = None
    random_image = None
    if search_term is not None:
        # TODO: Move the retry count to the config
        for i in range(0, 15):
            source = get_random_source(sources)
            try:
                random_image = source.get_random_search_image(text=search_term)
            except NoPhotosFoundException as ex:
                pass
            if source is not None and random_image is not None:
                break
        # If there was no search term or a search yielded no images
        if source is None or random_image is None:
            print("Couldn't find a suitable result for search term '%s'"%search_term)
            print("Posting reply to status id %s"%respond_to_id)
            twitter.post_text("Couldn't find your image. Try again!", respond_to_user=respond_to_user, respond_to_id=respond_to_id)
            return

    if random_image is None:
        source = get_random_source(sources)
        random_image = source.get_random_image()
        
    if random_image is None:        
        raise Exception("No images found")
    
    print("Selected Flickr ID: %s, Social User: %s" % (source.get_flickr_id(), twitter.get_social_id_from_source(source)))

    shortened_image_link = flickr.make_shortened_image_link(random_image)

    image_url_attribute = config.get("flickr", "flickr.image_url_attribute")
    if image_url_attribute in random_image:
        image_url = random_image[image_url_attribute]
    else:
        image_url = random_image["url_m"]

    image_title = random_image["title"]

    temp_jpg_file = "image_{pid}.jpg".format(pid=os.getpid())
    print("Selected image '%s' at %s" % (image_title, image_url))
    Util.fetch_image_to_path(image_url, temp_jpg_file)

    twitter.post_image(image_title, source, shortened_image_link, respond_to_user=respond_to_user, respond_to_id=respond_to_id, image_path=temp_jpg_file)

    if os.path.exists(temp_jpg_file):
        os.unlink(temp_jpg_file)



def check_translations(translations, mention_text, base_word="please"):
    """
    Iterates over the translated words and checks whether any exist within the text.
    Does not yet deal with alternate encoding.
    :param translations: A list of translations
    :param mention_text: The post text
    :param base_word: The word being translated. Must exist within the translations struct.
    :return: True if any of the translated words exist within the text
    """
    if base_word not in translations["translations"]:
        raise Exception("Baseword '%s' does not exist in the translation struct"%base_word)

    for translation in translations["translations"][base_word]:
        translation = translation.lower()
        if translation in mention_text:
            return True
    return False


def find_search_term_of(s, translations):
    for translation in translations["translations"]["of"]:
        m = re.search("(?<= %s )[ \w]+"%translation, s)
        if m is not None:
            return m
    return None


def find_search_term(s, translations):
    """
    Tries simple methods to determine a search term within a post. Partial support for i18n.
    :param s: The post text
    :return: The search term or None if one wasn't found.
    """
    m = find_search_term_of(s, translations)
    if m is None:
        return None
    t = m.group(0)
    if t is None or len(t) == 0:
        return None
    t = t.lower()
    t = re.sub(r"^(an|a|the) ", "", t)

    for translation in translations["translations"]["please"]:
        translation = translation.lower()
        t = re.sub(r" %s"%translation, "", t)

    t = t.strip()

    return t


def respond_to_mentions(config, sources, translations, flickr, twitter, since_id=None):
    """
    Checks for and responds to Twitter mentions asking for images. The mention must include 'please' or an internationalized translation
    of the word. It will also attempt (via a simple method) to determine if the user is searching for something specific and return
    a matching picture as found by Flickr's search algorithm.
    :param config: A configuration instance
    :param sources: A list of sources
    :param translations: A translations dict
    :param flickr: An instance of the Flickr API
    :param twitter: An instance of the Twitter API
    :param since_id: The last seen post id from the previous run
    :return: The highest id of the mentions processed during this run
    """
    mentions = twitter.get_mentions(since_id=since_id)

    id = since_id
    for mention in mentions:
        if mention["notification_id"] > id:
            id = mention["notification_id"]

        mention_text = mention["text"].lower()
        orig_mention_text = mention_text
        mention_text = re.sub('p+', 'p', mention_text)
        mention_text = re.sub('l+', 'l', mention_text)
        mention_text = re.sub('e+', 'e', mention_text)
        mention_text = re.sub('a+', 'a', mention_text)
        mention_text = re.sub('s+', 's', mention_text)
        respond_to_id = mention["status_id"]
        respond_to_user = "@%s" % mention["user"]["screen_name"]
        if check_translations(translations, mention_text) and mention["notification_id"] > since_id:
            search_term = find_search_term(orig_mention_text, translations)
            find_and_post_image(config, sources, flickr, twitter, search_term=search_term, respond_to_user=respond_to_user, respond_to_id=respond_to_id)
        if "status check" in mention_text and mention["notification_id"] > since_id:
            status = validate()
            twitter.post_text(status, respond_to_user=respond_to_user, respond_to_id=respond_to_id)
        if "fantastic, thank you" in mention_text and mention["notification_id"] > since_id:
            status = "You're welcome :-)"
            twitter.post_text(status, respond_to_user=respond_to_user, respond_to_id=respond_to_id)
    return id


def load_sources(source_file, flickr):
    """
    Loads a sources YAML file
    :param source_file: Path leading to a sources YAML file
    :param flickr: An initialized Flickr instance
    :return: A list of sources
    """
    sources = []
    with open(source_file) as f:
        d = f.read()
        sources_raw = yaml.load(d, Loader=Loader)
        for source_raw in sources_raw["sources"]:
            if "disabled" in source_raw and source_raw["disabled"] is True:
                continue
            sources.append(Source(source_raw, flickr))

    return sources


def load_translations(translations_file):
    """
    Loads a translations YAML file
    :param translations_file: Path leading to a translations YAML file
    :return: The translations
    """
    with open(translations_file) as f:
        d = f.read()
        translations = yaml.load(d, Loader=Loader)
    return translations


def get_random_source(sources):
    """
    Returns a random source from a list of sources
    :param sources: A list of sources
    :return: A random source
    """
    if sources is None or len(sources) == 0:
        raise Exception("No sources found")

    return sources[Util.randint(0, len(sources) - 1)]


def validate():
    """
    Performs a basic high-level validation of services
    :return: A string containing the validation results
    """
    conditions = []

    try:
        config = ConfigParser.RawConfigParser()
        config.read(args.config)
        conditions.append("Configuration: OK")
    except:
        conditions.append("Configuration: FAIL")

    try:
        flickr = Flickr(config)
        conditions.append("Flickr: OK")
    except:
        conditions.append("Flickr: FAIL")

    if flickr.verify_credentials():
        conditions.append("Flickr Test: OK")
    else:
        conditions.append("Flickr Test: FAIL")

    try:
        translations = load_translations(args.translations)
        conditions.append("Translations: OK")
    except:
        conditions.append("Translations: FAIL")

    try:
        sources = load_sources(args.sources, flickr)
        conditions.append("Sources: OK")
    except:
        conditions.append("Sources: FAIL")

    try:
        twitter = Twitter(config)
        conditions.append("Twitter: OK")
    except:
        conditions.append("Twitter: FAIL")

    if twitter.verify_credentials():
        conditions.append("Twitter Test: OK")
    else:
        conditions.append("Twitter Test: FAIL")

    return "\n".join(conditions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Specify an alternate configuration file", required=False, type=str, default="config.ini")
    parser.add_argument("-r", "--respond", help="Respond to Twitter mentions", action="store_true")
    parser.add_argument("-p", "--post", help="Post as status update", action="store_true")
    parser.add_argument("-s", "--sinceid", help="Most recent known mention id", required=False, type=int)
    parser.add_argument("-w", "--writeidto", help="Write most recent mention id to file", required=False, type=str)
    parser.add_argument("-S", "--sources", help="Specify an alternate sources yaml file", required=False, type=str, default="sources.yaml")
    parser.add_argument("-t", "--test", help="Run a status check", action="store_true")
    parser.add_argument("-i", "--translations", help="Specify an alternate translations yaml file", required=False, type=str, default="translations.yaml")
    parser.add_argument("-d", "--destination", help="Destination social media (twitter, mastodon)", required=False, type=str, default="mastodon")
    args = parser.parse_args()

    if args.test:
        print(validate())
        sys.exit(0)

    config = ConfigParser()
    config.read(args.config)

    flickr = Flickr(config)
    if args.destination.lower() == "twitter":
        social = Twitter(config)
    elif args.destination.lower() == "mastodon":
        social = MastodonClient(config)
    else:
        raise Exception("Unsupported social media: %s"%args.destination)

    sources = load_sources(args.sources, flickr)
    translations = load_translations(args.translations)
    
    if args.respond is True:
        last_id = respond_to_mentions(config, sources, translations, flickr, social, args.sinceid)
        if last_id is not None and last_id > 0:
            print(last_id)
            if args.writeidto is not None:
                with open(args.writeidto, "w") as f:
                    f.write(str(last_id))

    if args.post is True:
        find_and_post_image(config, sources, flickr, social)
    

