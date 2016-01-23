#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Shows how to control GoogleScraper programmatically.
"""

import sys
import json
import optparse
from pprint import pprint
from GoogleScraper import scrape_with_config, GoogleSearchError

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to scrape")
optparser.add_option("-n", "--num_images", dest="num_images", default=50, type=int, help="Number of images to harvest per word")
optparser.add_option("-d", "--dictionary", dest="dictionary", default="dict.fr", help="Google languages json file")
optparser.add_option("-L", "--language-map", dest="language_map", default="google-languages.json", help="Google languages json file")
(opts, _) = optparser.parse_args()

# read in the json file with the arguments (hl and lr) for each language in google
with open(opts.language_map, encoding='utf-8') as data_file:
    full_language_arg_map = json.loads(data_file.read())

# pull the foreign words out of the bilingual dictionary, this assumes the format foreign\tenglish\n
foreign_word_list = [line.strip().split('\t')[0] for line in open(opts.dictionary)]




### EXAMPLES OF HOW TO USE GoogleScraper ###

target_directory = 'images/'

print(foreign_word_list[5])

# See in the config.cfg file for possible values
config = {
    'keyword': foreign_word_list[5], # :D hehe have fun my dear friends
    'search_engines': ['google'],#'yandex', 'google', 'bing', 'yahoo'], # duckduckgo not supported
    'search_type': 'image',
    'scrape_method': 'selenium',
    'sel_browser': 'firefox',
    'do_caching': False
}

try:
    search = scrape_with_config(config)
    print(search)
except GoogleSearchError as e:
    print(e)

image_urls = []

for serp in search.serps:
    image_urls.extend(
        [link.link for link in serp.links]
    )

print('[i] Going to scrape {num} images and saving them in "{dir}"'.format(
    num=len(image_urls),
    dir=target_directory
))

import threading,requests, os, urllib

# In our case we want to download the
# images as fast as possible, so we use threads.
class FetchResource(threading.Thread):
    """Grabs a web resource and stores it in the target directory.
    Args:
        target: A directory where to save the resource.
        urls: A bunch of urls to grab
    """
    def __init__(self, target, urls):
        super().__init__()
        self.target = target
        self.urls = urls

    def run(self):
        for url in self.urls:
            url = urllib.parse.unquote(url)
            with open(os.path.join(self.target, url.split('/')[-1]), 'wb') as f:
                try:
                    content = requests.get(url).content
                    f.write(content)
                except Exception as e:
                    pass
                print('[+] Fetched {}'.format(url))

# make a directory for the results
try:
    os.mkdir(target_directory)
except FileExistsError:
    pass

# fire up 100 threads to get the images
num_threads = 100

threads = [FetchResource('images/', []) for i in range(num_threads)]

while image_urls:
    for t in threads:
        try:
            t.urls.append(image_urls.pop())
        except IndexError as e:
            break

threads = [t for t in threads if t.urls]

for t in threads:
    t.start()

for t in threads:
    t.join()

# that's it :)