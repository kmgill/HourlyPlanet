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
from TwitterAPI import TwitterAPI
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
    def __init__(self, config):
        self.__apikey = config.get("flickr", "flickr.key")
        self.page_size = config.get("flickr", "flickr.page_size")

    def get_user_info(self, user_id):
        resp = requests.get("https://www.flickr.com/services/rest/", params={
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
        resp = requests.get("https://www.flickr.com/services/rest/", params={
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

    @staticmethod
    def make_image_link(image):
        return "https://www.flickr.com/photos/{userid}/{photoid}".format(userid=image["owner"],
                                                                         photoid=image["id"])

    @staticmethod
    def make_shortened_image_link(image):
        return "https://flic.kr/p/{base58photoid}".format(base58photoid=Util.encode_base58(int(image["id"])))


class Twitter:

    def __init__(self, config):
        self.__api = TwitterAPI(config.get("twitter", "twitter.consumer_key"),
                                config.get("twitter", "twitter.consumer_secret"),
                                config.get("twitter", "twitter.access_token"),
                                config.get("twitter", "twitter.access_secret"))

    def tweet_image(self, title, username, twitter_id, shortened_image_link, imagePath="image.jpg"):
        text = "%s - From %s (%s) - %s"%(title, username, twitter_id, shortened_image_link)

        data = Util.load_image_data(imagePath)

        r = self.__api.request('media/upload', None, {'media': data})
        print('UPLOAD MEDIA SUCCESS' if r.status_code == 200 else 'UPLOAD MEDIA FAILURE: ' + r.text)

        if r.status_code == 200:
            media_id = r.json()['media_id']
            r = self.__api.request('statuses/update', {'status': text, 'media_ids': media_id})
            print('UPDATE STATUS SUCCESS' if r.status_code == 200 else 'UPDATE STATUS FAILURE: ' + r.text)


def main(config):

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

    print("Selected Flickr ID: %s, Twitter User: %s" % (flickr_id, twitter_id))

    flickr = Flickr(config)
    try:
        user_info = flickr.get_user_info(flickr_id)
    except:
        print("Failed to retrieve user information from Flickr")
        traceback.print_exc()
        sys.exit(1)

    user_name = user_info["person"]["realname"]["_content"]
    num_photos = user_info["person"]["photos"]["count"]["_content"]
    random_page = random.randint(0, int(math.ceil(float(num_photos) / float(flickr.page_size))))

    print("Flickr user %s has %s images, selected page %s" % (user_name, num_photos, random_page))

    try:
        ps_page = flickr.get_photostream(flickr_id, random_page)
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

    #image_link = flickr.make_image_link(random_image)
    shortened_image_link = flickr.make_shortened_image_link(random_image)
    image_url = random_image[config.get("flickr", "flickr.image_url_attribute")]
    image_title = random_image["title"]

    print("Selected image #%s '%s' at %s" % (random_image_num, image_title, image_url))
    Util.fetch_image_to_path(image_url, "image.jpg")

    twitter = Twitter(config)
    twitter.tweet_image(image_title, user_name, twitter_id, shortened_image_link)


if __name__ == "__main__":

    config = ConfigParser.RawConfigParser()
    config.read('config.ini')

    main(config)

