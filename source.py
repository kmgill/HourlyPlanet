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
import unidecode

from flickr import *


class Source:

    def __init__(self, source, flickr):
        self.__source = source
        self.__flickr = flickr

        try:
            self.__user_info = flickr.get_user_info(self.get_flickr_id())
        except:
            print("Failed to retrieve user information from Flickr")
            traceback.print_exc()
            raise Exception()

    def get_album_list(self):
        if "albums" not in self.__source:
            return []
        else:
            return map(str, self.__source["albums"])

    def pick_random_album_in_source(self):
        """
        Picks a random album from a list of albums. Raises an exception if there are no albums
        :return: An album
        """
        if "albums" not in self.__source:
            raise Exception("No albums found for source")

        return self.__source["albums"][Util.randint(0, len(self.__source["albums"]) - 1)]

    def get_twitter_id(self):
        """
        Returns the source's twitter id
        :return: The source's twitter id
        """
        if "twitter_id" in self.__source:
            return self.__source["twitter_id"]
        else:
            return ""

    def get_mastodon_id(self):
        if "mastodon_id" in self.__source:
            return self.__source["mastodon_id"]
        else:
            return ""

    def get_flickr_id(self):
        """
        Returns the source's flickr id
        :return: The source's flickr id
        """
        return self.__source["flickr_id"]

    def get_flickr_username(self):
        """
        Returns the Flickr user's username. Attempts to use the 'realname' property, but will fall back to
        using the 'username' property.
        :return: The Flickr user's username
        """
        if self.__user_info["person"]["realname"]["_content"] is None or len(self.__user_info["person"]["realname"]["_content"]) == 0:
            return unidecode.unidecode(self.__user_info["person"]["username"]["_content"])
        else:
            return unidecode.unidecode(self.__user_info["person"]["realname"]["_content"])

    def user_has_albums(self):
        """
        Returns true if the source has configured albums. Does not check whether the user actually has albums on Flickr.
        :return: true if the source has configured albums
        """
        return "albums" in self.__source and len(self.__source["albums"]) > 0

    def get_random_album(self):
        """
        Returns a random album from a list of configured albums. Does not check for additional albums on Flickr for
        the user.
        :return: A random album from a list of configured albums.
        """
        if not self.user_has_albums():
            raise NoAlbumsFoundException("Cannot get random album if user has not albums.")

        if len(self.__source["albums"]) == 0:
            raise NoAlbumsFoundException("User has no albums")

        random_album_id = self.__source["albums"][Util.randint(0, len(self.__source["albums"]) - 1)]
        album_info = self.__flickr.get_album_info(self.get_flickr_id(), random_album_id)
        return album_info

    def get_random_image(self):
        if self.user_has_albums():
            album_info = self.get_random_album()
            random_image = self.get_random_album_image(album_info)
        else:
            random_image = self.get_random_photoset_image()

        return random_image

    def get_random_search_image(self, text):
        search_photos = self.__flickr.search_user_photos(self.get_flickr_id(), text, page_size=0)
        num_photos = int(search_photos["photos"]["total"])
        random_page = Util.randint(0, int(math.ceil(float(num_photos) / float(self.__flickr.page_size))))
        user_name = self.get_flickr_username()
        
        print("Flickr user %s has %s images matching search, selected page %s" % (user_name, num_photos, random_page))

        try:
            ps_page = self.__flickr.search_user_photos(self.__user_info["person"]["id"], text, random_page)
        except:
            print("Failed to retrieve user search from Flickr")
            traceback.print_exc()
            raise Exception("Failed to retrieve user search from Flickr")

        

        num_images = len(ps_page["photos"]["photo"])
        if num_images == 0:
            print("Page has zero images, cannot continue")
            raise NoPhotosFoundException("Page has zero images, cannot continue")

        random_image_num = Util.randint(0, num_images - 1)
        random_image = ps_page["photos"]["photo"][random_image_num]
    
        # If the source has albums specified, we need to make sure we are only 
        # picking from those. The Flickr search call doesn't let us limit to
        # specific albums so we need to verify manually
        if self.user_has_albums() is True:
            if self.__flickr.photo_is_in_albums(random_image["id"], self.get_album_list()) is False:
                raise NoPhotosFoundException("Found image is not part of valid album")
    
        return random_image


    def get_random_photoset_image(self):
        num_photos = self.__user_info["person"]["photos"]["count"]["_content"]
        random_page = Util.randint(0, int(math.ceil(float(num_photos) / float(self.__flickr.page_size))))
        user_name = self.get_flickr_username()

        print("Flickr user %s has %s images, selected page %s" % (user_name, num_photos, random_page))

        try:
            ps_page = self.__flickr.get_photostream(self.__user_info["person"]["id"], random_page)
        except:
            print("Failed to retrieve user Photostream from Flickr")
            traceback.print_exc()
            raise Exception("Failed to retrieve user Photostream from Flickr")

        num_images = len(ps_page["photos"]["photo"])
        if num_images == 0:
            print("Page has zero images, cannot continue")
            raise NoPhotosFoundException("Page has zero images, cannot continue")

        random_image_num = Util.randint(0, num_images - 1)
        random_image = ps_page["photos"]["photo"][random_image_num]

        return random_image

    def get_random_album_image(self, album_info):
        num_photos = album_info["photoset"]["photos"]
        random_page = Util.randint(0, int(math.ceil(float(num_photos) / float(self.__flickr.page_size))))

        user_name = self.get_flickr_username()
        album_name = album_info["photoset"]["title"]["_content"]
        print("Flickr album %s for user %s has %s images, selected page %s" % (
        album_name, user_name, num_photos, random_page))

        try:
            al_page = self.__flickr.get_album_photos(self.__user_info["person"]["id"], album_info["photoset"]["id"], random_page)
        except:
            print("Failed to retrieve user album from Flickr")
            raise Exception("Failed to retrieve user album from Flickr")

        num_images = len(al_page["photoset"]["photo"])
        if num_images == 0:
            print("Page has zero images, cannot continue")
            raise NoPhotosFoundException("Page has zero images, cannot continue")

        random_image_num = Util.randint(0, num_images - 1)
        random_image = al_page["photoset"]["photo"][random_image_num]

        return random_image
