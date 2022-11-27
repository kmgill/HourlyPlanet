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
from TwitterAPI import TwitterAPI
import argparse
import re
import yaml
from util import Util

class Twitter:
    """
    Simplified proxy to TwitterAPI implementing functions required by the application
    """

    def __init__(self, config):
        self.__api = TwitterAPI(config.get("twitter", "twitter.consumer_key"),
                                config.get("twitter", "twitter.consumer_secret"),
                                config.get("twitter", "twitter.access_token"),
                                config.get("twitter", "twitter.access_secret"))

    def get_social_id_from_source(self, source):
        return  source.get_twitter_id()

    def verify_credentials(self):
        """
        Validates current API credentials
        :return: True if an HTTP status code of 200 is returned from Twitter
        """
        r = self.__api.request('account/verify_credentials')
        return r.status_code == 200

    def post_text(self, status, respond_to_user=None, respond_to_id=None):
        """
        Sends a text-only tweet
        :param status: The tweet text to be posted
        :param respond_to_user: User being responded to. None if not a response.
        :param respond_to_id: Tweet being responded to. None if not a response.
        :return: True if the Twitter API returned an HTTP 200 status.
        """
        if respond_to_user is not None:
            status = "Hi, %s\n\n%s"%(respond_to_user, status)
        r = self.__api.request('statuses/update',
                               {'status': status, 'in_reply_to_status_id': respond_to_id})
        print('UPDATE STATUS SUCCESS' if r.status_code == 200 else 'UPDATE STATUS FAILURE: ' + r.text)


    def post_image(self, title, source, shortened_image_link, image_path="image.jpg", respond_to_user=None, respond_to_id=None):
        """
        Tweets an image and Flickr photo title
        :param title: The photo title
        :param source: The Flickr source dict
        :param shortened_image_link: A URL to the source image on Flickr
        :param image_path: A path to the image to be tweeted
        :param respond_to_user: A user to be responded to. None if not a response.
        :param respond_to_id: ID of the tweet being responded to. None if not a response.
        :return: True if the Twitter API returned an HTTP 200 status.
        """
        username = source.get_flickr_username()
        twitter_id = source.get_twitter_id()
        
        twitter_id = "" if twitter_id is None or len(twitter_id) == 0 else "(%s)"%twitter_id
        
        if respond_to_user is None:
            text = "%s - From %s %s - %s"%(title, username, twitter_id, shortened_image_link)
        else:
            text = "Hi, %s\n\n%s - From %s %s - %s" % (respond_to_user, title, username, twitter_id, shortened_image_link)

        data = Util.load_image_data(image_path)

        r = self.__api.request('media/upload', None, {'media': data})
        print('UPLOAD MEDIA SUCCESS' if r.status_code == 200 else 'UPLOAD MEDIA FAILURE: ' + r.text)

        if r.status_code == 200:
            media_id = r.json()['media_id']
            r = self.__api.request('statuses/update', {'status': text, 'media_ids': media_id, 'in_reply_to_status_id': respond_to_id})
            print('UPDATE STATUS SUCCESS' if r.status_code == 200 else 'UPDATE STATUS FAILURE: ' + r.text)

    def get_mentions(self, since_id=None, count=100):
        """
        Retrieves a list of recent Twitter mentions since the ID of the provided tweet.
        :param since_id: An identifier of the last reviewed mention (on last run)
        :param count: A maximum of mentioned to be returned by the API
        :return: A list of tweets
        """
        params = {'count':count}
        if since_id is not None and since_id > 0:
            params["since_id"] = since_id

        r = self.__api.request('statuses/mentions_timeline', params)
        if r.status_code != 200:
            print('retrieval failure: ' + r.text)
            raise Exception('retrieval failure: ' + r.text)

        mentions = []
        for mention in r.json():
            mentions.append({
                "status_id": mention["id"],
                "notification_id": mention["id"],
                "text": mention["text"],
                "user": {
                    "screen_name":  mention["user"]["screen_name"]
                }
            })
        return mentions


