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


class Util:
    """
    Basic static utility functions
    """

    __alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    __base_count = len(__alphabet)

    @staticmethod
    def randint(min=0, max=255):
        """
        Returns a random integer between the specified min and max, inclusive of both
        """
        print("Finding random between %f and %f"%(min, max))
        if min == max:
            return min
        elif max == 0:
            return 0
        else:
            return int(round((os.urandom(1)[0]) / 255.0 * (max - min) + min))

    # https://gist.github.com/ianoxley/865912
    @staticmethod
    def encode_base58(num):
        if type(num) != int and type(num) != long :
            raise TypeError("Value must be an integer")
        encode = ''
        if num < 0:
            return ''

        while num >= Util.__base_count:
            mod = num % Util.__base_count
            encode = Util.__alphabet[int(mod)] + encode
            num = num / Util.__base_count

        if num:
            encode = Util.__alphabet[int(num)] + encode

        return encode

    @staticmethod
    def load_image_data(path):
        if not os.path.exists(path):
            raise IOError("Path not found: %s, Cannot load image"%path)

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
