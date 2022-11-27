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

from mastodon import Mastodon
from util import Util

class MastodonClient:
    def __init__(self, config):
        self.mastodon = Mastodon(
                                access_token=config.get("mastodon", "mastodon.access_token"),
                                api_base_url=config.get("mastodon", "mastodon.baseurl"))

    def get_social_id_from_source(self, source):
        return source.get_mastodon_id()

    def verify_credentials(self):
        pass

    def post_text(self, status, respond_to_user=None, respond_to_id=None, media_id=None):
        if respond_to_id is None:
            self.mastodon.status_post(status, media_ids=[media_id])
        else:
            status = "Hi, %s\n\n%s"%(respond_to_user, status)
            if media_id is not None:
                self.mastodon.status_reply(status, 
                                            in_reply_to_id=respond_to_id,
                                            media_ids=[media_id])
            else:
                self.mastodon.status_post(status, 
                                            in_reply_to_id=respond_to_id)
        """
        Mastodon.status_post(status, 
                                in_reply_to_id=None, 
                                media_ids=None, 
                                sensitive=False, 
                                visibility=None, 
                                spoiler_text=None, 
                                language=None, 
                                idempotency_key=None, 
                                content_type=None, 
                                scheduled_at=None, 
                                poll=None, 
                                quote_id=None)
        """

        """
        Mastodon.status_reply(to_status, 
                                status, 
                                in_reply_to_id=None, 
                                media_ids=None, 
                                sensitive=False, 
                                visibility=None, 
                                spoiler_text=None, 
                                language=None, 
                                idempotency_key=None, 
                                content_type=None, 
                                scheduled_at=None, 
                                poll=None, 
                                untag=False)
        """

    def post_image(self, title, source, shortened_image_link, image_path="image.jpg", respond_to_user=None, respond_to_id=None):

        username = source.get_flickr_username()
        mastodon_id = source.get_mastodon_id()
        
        mastodon_id = "" if mastodon_id is None or len(mastodon_id) == 0 else "(%s)"%mastodon_id
        
        if respond_to_user is None:
            text = "%s - From %s %s - %s"%(title, username, mastodon_id, shortened_image_link)
        else:
            text = "Hi, %s\n\n%s - From %s %s - %s" % (respond_to_user, title, username, mastodon_id, shortened_image_link)

        media = self.mastodon.media_post(image_path, "image/jpeg")
        # TODO: Error checking? Returned dict doesn't appear to have a status
        self.post_text(text, respond_to_user=None, respond_to_id=None, media_id=media["id"])




        

    def get_mentions(self, since_id=None, count=100):
        mentions_raw = self.mastodon.notifications(types=["mention"], limit=count, since_id=since_id)
        mentions = []
        for  mention in mentions_raw:
            mentions.append({
                "status_id": mention["status"]["id"],
                "notification_id": mention["id"],
                "text": mention["status"]["content"],
                "user": {
                    "screen_name":  mention["account"]["acct"]
                }
            })
        return mentions


