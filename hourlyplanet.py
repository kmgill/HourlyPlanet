"""
Copyright 2020 Kevin M. Gill

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
import requests
import ConfigParser
import math
import traceback
import json
from TwitterAPI import TwitterAPI
import argparse
import random
random.seed()



class Util:

    __alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    __base_count = len(__alphabet)

    # https://gist.github.com/ianoxley/865912
    @staticmethod
    def encode_base58(num):
        encode = ''
        if num < 0:
            return ''

        while num >= Util.__base_count:
            mod = num % Util.__base_count
            encode = Util.__alphabet[mod] + encode
            num = num / Util.__base_count

        if num:
            encode = Util.__alphabet[num] + encode

        return encode

    @staticmethod
    def load_image_data(path):
        with open(path, 'rb') as p:
            data = p.read()
        return data

    @staticmethod
    def fetch_image_to_path(url, path):
        print("Fetching %s to %s"%(url, path))
        r = requests.get(url, params={})
        if r.status_code != 200:
            raise Exception("Error fetching image. Status code: %s"%(r.status_code))
        with open(path, "wb") as f:
            f.write(r.content)
        return path


class Flickr:

    REST_BASE_URL = 'https://www.flickr.com/services/rest/'
    PHOTOS_URL_TEMPLATE = "https://www.flickr.com/photos/{userid}/{photoid}"
    PHOTOS_SHORTENED_URL_TEMPLATE = "https://flic.kr/p/{base58photoid}"

    def __init__(self, config):
        self.__apikey = config.get("flickr", "flickr.key")
        self.page_size = config.get("flickr", "flickr.page_size")

    def get_user_info(self, user_id):
        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.people.getInfo",
            "api_key": self.__apikey,
            "user_id": user_id,
            "format": "json",
            "nojsoncallback": 1
        })

        if resp.status_code != 200:
            raise Exception("Error fetching Flickr user information. Status code: %s"%(resp.status_code))

        user_info = resp.json()

        if user_info["stat"] != "ok":
            raise Exception("Error fetching Flickr user information. Reason: %s"%user_info["message"])

        return user_info

    def get_photostream(self, user_id, page=1):
        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.people.getPublicPhotos",
            "api_key": self.__apikey,
            "user_id": user_id,
            "format": "json",
            "nojsoncallback": 1,
            "extras": " url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o,description,tags,owner_name",
            "per_page": self.page_size,
            "page": page
        })

        if resp.status_code != 200:
            raise Exception("Error fetching Flickr photostream list. Status code: %s"%(resp.status_code))

        ps = resp.json()

        if ps["stat"] != "ok":
            raise Exception("Error fetching Flickr photostream. Reason: %s"%ps["message"])

        return ps

    def get_group_photos(self, group_id, page=1):
        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.groups.pools.getPhotos",
            "api_key": self.__apikey,
            "group_id": group_id,
            "format": "json",
            "nojsoncallback": 1,
            "extras": " url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o,description,tags,owner_name,license",
            "per_page": self.page_size,
            "page": page
        })

        if resp.status_code != 200:
            raise Exception("Error fetching Flickr group photo list. Status code: %s"%(resp.status_code))

        ps = resp.json()

        if ps["stat"] != "ok":
            raise Exception("Error fetching Flickr group photo list. Reason: %s"%ps["message"])

        return ps


    @staticmethod
    def make_image_link(image):
        return Flickr.PHOTOS_URL_TEMPLATE.format(userid=image["owner"],
                                                                         photoid=image["id"])

    @staticmethod
    def make_shortened_image_link(image):
        return Flickr.PHOTOS_SHORTENED_URL_TEMPLATE.format(base58photoid=Util.encode_base58(int(image["id"])))


class Twitter:

    def __init__(self, config):
        self.__api = TwitterAPI(config.get("twitter", "twitter.consumer_key"),
                                config.get("twitter", "twitter.consumer_secret"),
                                config.get("twitter", "twitter.access_token"),
                                config.get("twitter", "twitter.access_secret"))

    def tweet_image(self, title, username, twitter_id, shortened_image_link, imagePath="image.jpg", respond_to_user=None, respond_to_id=None):

        if respond_to_user is None:
            text = "%s - From %s (%s) - %s"%(title, username, twitter_id, shortened_image_link)
        else:
            text = "Hi, %s\n\n%s - From %s (%s) - %s" % (respond_to_user, title, username, twitter_id, shortened_image_link)

        data = Util.load_image_data(imagePath)

        r = self.__api.request('media/upload', None, {'media': data})
        print('UPLOAD MEDIA SUCCESS' if r.status_code == 200 else 'UPLOAD MEDIA FAILURE: ' + r.text)

        if r.status_code == 200:
            media_id = r.json()['media_id']
            r = self.__api.request('statuses/update', {'status': text, 'media_ids': media_id, 'in_reply_to_status_id': respond_to_id})
            print('UPDATE STATUS SUCCESS' if r.status_code == 200 else 'UPDATE STATUS FAILURE: ' + r.text)

    def get_mentions(self, since_id=None, count=100):

        params = {'count':count}
        if since_id is not None and since_id > 0:
            params["since_id"] = since_id

        r = self.__api.request('statuses/mentions_timeline', params)
        if r.status_code != 200:
            print('retrieval failure: ' + r.text)
            raise Exception('retrieval failure: ' + r.text)
        return r.json()




def get_random_person(config, flickr):
    """
    User Ids need to be a comma delimited list, no spaces. Each is is a colon (:) delimited list of Flickr ID and Twitter username
    Example:

    [people]
    people.user_ids=53460575@N03:@kevinmgill,136797589@N04:@_TheSeaning
    """
    user_ids = config.get("people", "people.user_ids")
    user_ids = user_ids.split(",")
    user_id = user_ids[random.randint(0, len(user_ids) - 1)]

    flickr_id = user_id.split(":")[0]
    twitter_id = user_id.split(":")[1]

    try:
        user_info = flickr.get_user_info(flickr_id)
    except:
        print("Failed to retrieve user information from Flickr")
        traceback.print_exc()
        sys.exit(1)

    return flickr_id, twitter_id, user_info

def get_random_image(user_info, flickr):
    num_photos = user_info["person"]["photos"]["count"]["_content"]
    random_page = random.randint(0, int(math.ceil(float(num_photos) / float(flickr.page_size))))
    user_name = user_info["person"]["realname"]["_content"]

    print("Flickr user %s has %s images, selected page %s" % (user_name, num_photos, random_page))

    try:
        ps_page = flickr.get_photostream(user_info["person"]["id"], random_page)
    except:
        print("Failed to retrieve user Photostream from Flickr")
        traceback.print_exc()
        sys.exit(1)

    num_images = len(ps_page["photos"]["photo"])
    if num_images == 0:
        print("Page has zero images, cannot continue")
        sys.exit(1)

    random_image_num = random.randint(0, num_images - 1)
    random_image = ps_page["photos"]["photo"][random_image_num]

    return random_image

def find_and_tweet_image(config, flickr, twitter, respond_to_user=None, respond_to_id=None):


    flickr_id, twitter_id, user_info = get_random_person(config, flickr)
    print("Selected Flickr ID: %s, Twitter User: %s" % (flickr_id, twitter_id))

    random_image = get_random_image(user_info, flickr)

    user_name = user_info["person"]["realname"]["_content"]
    #image_link = flickr.make_image_link(random_image)
    shortened_image_link = flickr.make_shortened_image_link(random_image)
    image_url = random_image[config.get("flickr", "flickr.image_url_attribute")]
    image_title = random_image["title"]

    print("Selected image '%s' at %s" % (image_title, image_url))
    Util.fetch_image_to_path(image_url, "image.jpg")

    twitter.tweet_image(image_title, user_name, twitter_id, shortened_image_link, respond_to_user=respond_to_user, respond_to_id=respond_to_id)


def respond_to_mentions(config, flickr, twitter, since_id=None):
    mentions = twitter.get_mentions(since_id=since_id)

    id = 0
    for mention in mentions:
        if mention["id"] > id:
            id = mention["id"]
        if "please" in mention["text"].lower():
            respond_to_id = mention["id"]
            respond_to_user = "@%s"%mention["user"]["screen_name"]
            find_and_tweet_image(config, flickr, twitter, respond_to_user=respond_to_user, respond_to_id=respond_to_id)
    return id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Specify an alternate configuration file", required=False, type=str, default="config.ini")
    parser.add_argument("-r", "--respond", help="Respond to Twitter mentions", action="store_true")
    parser.add_argument("-p", "--post", help="Post as status update", action="store_true")
    parser.add_argument("-s", "--sinceid", help="Most recent known mention id", required=False, type=int)
    parser.add_argument("-w", "--writeidto", help="Write most recent mention id to file", required=False, type=str)
    args = parser.parse_args()


    config = ConfigParser.RawConfigParser()
    config.read(args.config)

    flickr = Flickr(config)
    twitter = Twitter(config)

    if args.respond is True:
        last_id = respond_to_mentions(config, flickr, twitter, since_id=args.sinceid)
        if last_id is not None and last_id > 0:
            print last_id
            if args.writeidto is not None:
                with open(args.writeidto, "w") as f:
                    f.write(str(last_id))


    if args.post is True:
        find_and_tweet_image(config, flickr, twitter)

