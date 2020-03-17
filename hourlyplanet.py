import requests
import json
import ConfigParser
import math
from TwitterAPI import TwitterAPI
import random
random.seed()

alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
base_count = len(alphabet)

# https://gist.github.com/ianoxley/865912
def encode_base58(num):
    encode = ''
    if num < 0:
        return ''

    while num >= base_count:
        mod = num % base_count
        encode = alphabet[mod] + encode
        num = num / base_count

    if num:
        encode = alphabet[num] + encode

    return encode

def get_flickr_user_info(apikey, user_id):
    resp = requests.get("https://www.flickr.com/services/rest/", params={
        "method": "flickr.people.getInfo",
        "api_key": apikey,
        "user_id": user_id,
        "format": "json",
        "nojsoncallback": 1
    })
    return resp.json()


def get_flickr_photostream(apikey, user_id, page=1):
    resp = requests.get("https://www.flickr.com/services/rest/", params={
        "method": "flickr.people.getPublicPhotos",
        "api_key": apikey,
        "user_id": user_id,
        "format": "json",
        "nojsoncallback": 1,
        "extras": " url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o,description,tags,owner_name",
        "per_page": 100,
        "page": page
    })
    return resp.json()

def fetch_image_to_path(uri, path):
    url = uri
    print "Fetching", url
    params = {
    }
    r = requests.get(url, params=params)
    print url, r.status_code, r.history
    f = open(path, "wb")
    f.write(r.content)
    f.close()
    return path


def tweet_image(api, title, username, twitter_id, shortened_image_link, imagePath="image.jpg"):
    text = "%s - From %s (%s) - %s"%(title, username, twitter_id, shortened_image_link)
    photo = open(imagePath, 'rb')
    data = photo.read()
    photo.close()

    r = api.request('media/upload', None, {'media': data})
    print('UPLOAD MEDIA SUCCESS' if r.status_code == 200 else 'UPLOAD MEDIA FAILURE: ' + r.text)

    if r.status_code == 200:
        media_id = r.json()['media_id']
        r = api.request('statuses/update', {'status': text, 'media_ids': media_id})
        print('UPDATE STATUS SUCCESS' if r.status_code == 200 else 'UPDATE STATUS FAILURE: ' + r.text)


config = ConfigParser.RawConfigParser()
config.read('config.ini')

user_ids = config.get("flickr", "flickr.user_ids")
user_ids = user_ids.split(",")
user_id = user_ids[random.randint(0, len(user_ids) - 1)]

flickr_id = user_id.split(":")[0]
twitter_id = user_id.split(":")[1]

apikey = config.get("flickr", "flickr.key")

user_info = get_flickr_user_info(apikey, flickr_id)

user_name = user_info["person"]["realname"]["_content"]
num_photos = user_info["person"]["photos"]["count"]["_content"]
random_page = random.randint(0, int(math.ceil(float(num_photos)/100.0)))

ps_page = get_flickr_photostream(apikey, flickr_id, random_page)
num_images = len(ps_page["photos"]["photo"])
random_image_num = random.randint(0, num_images - 1)
random_image = ps_page["photos"]["photo"][random_image_num]

image_link = "https://www.flickr.com/photos/{userid}/{photoid}".format(userid=random_image["owner"],photoid=random_image["id"])
shortened_image_link = "https://flic.kr/p/{base58photoid}".format(base58photoid=encode_base58(int(random_image["id"])))

image_title = random_image["title"]
fetch_image_to_path(random_image["url_z"], "image.jpg")

api = TwitterAPI(config.get("twitter", "twitter.consumer_key"),
                 config.get("twitter", "twitter.consumer_secret"),
                 config.get("twitter", "twitter.access_token"),
                 config.get("twitter", "twitter.access_secret"))

tweet_image(api, image_title, user_name, twitter_id, shortened_image_link)
