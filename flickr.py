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
from util import Util


class NoPhotosFoundException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class NoAlbumsFoundException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)



class Flickr:
    """
    Lightweight Flickr API implementation
    """

    REST_BASE_URL = 'https://www.flickr.com/services/rest/'
    PHOTOS_URL_TEMPLATE = "https://www.flickr.com/photos/{userid}/{photoid}"
    PHOTOS_SHORTENED_URL_TEMPLATE = "https://flic.kr/p/{base58photoid}"

    def __init__(self, config):
        self.__apikey = config.get("flickr", "flickr.key")
        self.page_size = config.get("flickr", "flickr.page_size")

    def verify_credentials(self):
        """
        Simple method to verify the Flickr API key is still active and allowed.
        :return: True if the response received an HTTP status code of 200
        """
        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.test.echo",
            "api_key": self.__apikey,
            "format": "json",
            "nojsoncallback": 1
        })
        return resp.status_code == 200

    def get_user_info(self, user_id):
        """
        Fetches information about a Flickr user
        :param user_id: Flickr numeric id
        :return: information about a Flickr user
        """
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
    
    def get_photo_contexts(self, photo_id):
        """
        Fetches info on a particular photo
        """
        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.photos.getAllContexts",
            "api_key": self.__apikey,
            "photo_id": photo_id,
            "format": "json",
            "nojsoncallback": 1
        })
        
        if resp.status_code != 200:
            raise Exception("Error fetching Flickr photo context information. Status code: %s"%(resp.status_code))
        
        photo_info = resp.json()
        
        if photo_info["stat"] != "ok":
            raise Exception("Error fetching Flickr photo context information. Reason: %s"%photo_info["message"])

        return photo_info 
    
    
    def photo_is_in_albums(self, photo_id, album_ids):
        sets = self.get_photo_contexts(photo_id)
        if "set" not in sets:
            return False
        for album in sets["set"]:
            if album["id"] in album_ids:
                return True
        return False
    
    def get_photo_info(self, photo_id):
        """
        Fetches info on a particular photo
        """
        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.photos.getInfo",
            "api_key": self.__apikey,
            "photo_id": photo_id,
            "format": "json",
            "nojsoncallback": 1
        })
        
        if resp.status_code != 200:
            raise Exception("Error fetching Flickr photo information. Status code: %s"%(resp.status_code))
        
        photo_info = resp.json()
        
        if photo_info["stat"] != "ok":
            raise Exception("Error fetching Flickr photo information. Reason: %s"%photo_info["message"])

        return photo_info 
    
    def search_user_photos(self, user_id, text, page=1, page_size=None):
        """
        Searches user photostream photos using full-text search
        :param user_id: Flickr numeric id
        :param text: Full-text search term
        :param page: Results page number
        :param page_size: Number of results per page (default determined by config.ini)
        :return: A list of matching photos
        """

        if text is None or len(text) == 0:
            raise Exception("Invalid zero-length search term used.")

        if page_size is None:
            page_size = self.page_size

        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.photos.search",
            "api_key": self.__apikey,
            "user_id": user_id,
            "text": text,
            "format": "json",
            "nojsoncallback": 1,
            "privacy_filter": 1,
            "extras": " url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o,description,tags,owner_name",
            "per_page": page_size,
            "page": page
        })
        if resp.status_code != 200:
            raise Exception("Error fetching Flickr search list. Status code: %s"%(resp.status_code))

        ps = resp.json()

        if ps["stat"] != "ok":
            raise Exception("Error fetching Flickr search. Reason: %s"%ps["message"])

        return ps

    def get_photostream(self, user_id, page=1):
        """
        Fetches images from a Flickr user's photostream
        :param user_id: Flickr numeric id
        :param page: Results page number
        :return: A list of photos
        """
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
        """
        Fetches photos from a Flickr group pool
        :param group_id: Group id
        :param page: Results page number
        :return: A list of photos
        """

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
    
    
    def get_album_info(self, user_id, photoset_id):
        """
        Fetches information about a Flickr album
        :param user_id: Flickr numeric id
        :param photoset_id: Flickr album numeric id
        :return: Information about the Flickr album
        """

        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.photosets.getInfo",
            "api_key": self.__apikey,
            "user_id": user_id,
            "photoset_id": photoset_id,
            "format": "json",
            "nojsoncallback": 1
        })
        if resp.status_code != 200:
            raise Exception("Error fetching Flickr album info. Status code: %s"%(resp.status_code))

        ps = resp.json()

        if ps["stat"] != "ok":
            raise Exception("Error fetching Flickr album info. Reason: %s"%ps["message"])

        return ps

    def get_album_photos(self, user_id, photoset_id, page=1):
        """
        Fetches photos from a Flickr album
        :param user_id: A Flickr numeric user id
        :param photoset_id: Flickr album numeric album id
        :param page: Results page number
        :return: A list of photos
        """

        resp = requests.get(Flickr.REST_BASE_URL, params={
            "method": "flickr.photosets.getPhotos",
            "api_key": self.__apikey,
            "user_id": user_id,
            "photoset_id": photoset_id,
            "format": "json",
            "nojsoncallback": 1,
            "extras": " url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o,description,tags,owner_name,license",
            "per_page": self.page_size,
            "page": page
        })

        if resp.status_code != 200:
            raise Exception("Error fetching Flickr album photo list. Status code: %s"%(resp.status_code))

        ps = resp.json()

        if ps["stat"] != "ok":
            raise Exception("Error fetching Flickr album photo list. Reason: %s"%ps["message"])

        return ps

    @staticmethod
    def make_image_link(image):
        """
        Builds a full Flickr image page link
        :param image: Image info dict
        :return: A URL to the image on Flickr
        """

        return Flickr.PHOTOS_URL_TEMPLATE.format(userid=image["owner"],
                                                                         photoid=image["id"])

    @staticmethod
    def make_shortened_image_link(image):
        """
        Builds a shortened Flickr image page link
        :param image: Image info dict
        :return: A shortened URL to the image on Flickr
        """

        return Flickr.PHOTOS_SHORTENED_URL_TEMPLATE.format(base58photoid=Util.encode_base58(int(image["id"])))
