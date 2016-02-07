import time
import os
import re
import urllib.request
import shutil
import json
import optparse
import boto3
import socket

from selenium import webdriver

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to scrape")
optparser.add_option("-n", "--num_images", dest="num_images", default=100, type=int, help="Number of images to harvest per word")
optparser.add_option("-d", "--dictionary", dest="dictionary", default="dict.fr", help="Google languages json file")
optparser.add_option("-L", "--language-map", dest="language_map", default="google-languages.json", help="Google languages json file")
optparser.add_option("-s", "--start_index", dest="start_index", default=None, type=int, help="Word index to start iterating at")
(opts, _) = optparser.parse_args()

# tbm=isch sets this to be image search, start=0 will give us 100 results on page 1
BASE_GOOGLE_IMAGE_SEARCH_LINK = 'https://www.google.com/search?#tbm=isch&start=0'

# regex for extracting source link component: http://www.inddist.com/sites/inddist.com/files/Dollar-Sign.jpg
# from compound links like:
# https://www.google.com/imgres?imgurl=http://www.inddist.com/sites/inddist.com/files/Dollar-Sign.jpg&imgrefurl=http://www.inddist.com/article/2015/05/put-dollar-sign-next-your-service-value&h=1600&w=1200&tbnid=9XAphqXNraTVnM:&docid=Hm9c-cTh-Hl_DM&ei=43-xVsTKMsixeNrCoNAL&tbm=isch&ved=0ahUKEwiEyMjt3trKAhXIGB4KHVohCLoQMwgdKAAwAA
IMAGE_URL_REGEX = r'imgres\?imgurl=(?P<url>.*?)&'

# XPATH statement that finds all of the links on the page that correspond to the original image links
# this is probably subject to change on google's part
GOOGLE_IMAGE_LINK_XPATH = "//a[@class='rg_l']"

BASE_IMAGE_PATH = 'images/'
S3_BUCKET_NAME = 'brendan.callahan'
S3_BASE_PATH = 'thesis/images/'+opts.language+'/'
STORAGE_MODE = 'S3' # or 'FILESYSTEM'
DEBUG_MODE = False
VERBOSE_MOSE = True

# read in the json file with the arguments (hl and lr) for each language in google
with open(opts.language_map, encoding='utf-8') as data_file:
    full_language_arg_map = json.loads(data_file.read())

# pull the foreign words out of the bilingual dictionary, this assumes the format foreign\tenglish\n
foreign_word_list = [line.strip().split('\t')[0] for line in open(opts.dictionary)]


# creates a selenium browser instance with Firefox
def create_selenium_browser():
    driver = webdriver.Firefox()
    driver.implicitly_wait(10)#10 is arbitrary
    return driver


# takes the link element from xpath, dissects out the href attribute, and runs a regex to extract the source URL
def get_image_link(link_element):
    href = link_element.get_attribute('href')
    regex_result = re.search(IMAGE_URL_REGEX, href)
    return regex_result.group('url')


# takes the image link, pulls out the filename, downloads it. when in S3 mode, it will push the result onto S3 as well
def download_image(actual_image_link, word_index):
    actual_file_name = actual_image_link.split('/')[-1]
    if VERBOSE_MOSE: print('Downloading... ' + actual_image_link)

    # ggpht images seem to be internal to the search engine results, skipping them
    if actual_image_link.find('ggpht.com/') == -1:
        full_path = BASE_IMAGE_PATH+actual_file_name
        try:
            with urllib.request.urlopen(actual_image_link, timeout=30) as response, open(full_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            # when S3 mode is turned on, upload the file over to S3 and delete the local copy
            # TODO can we simplify this so it doesn't need to write out to a tmp location?
            # TODO add metadata like original link to storage?
            if STORAGE_MODE == 'S3':
                word_index_str = "{0:0=2d}".format(word_index)
                destination_path = S3_BASE_PATH+word_index_str+'/'+actual_file_name
                s3_client = boto3.resource('s3')
                s3_client.meta.client.upload_file(full_path, S3_BUCKET_NAME, destination_path)
                os.remove(full_path)

        # catch some 503/504 type errors and also if the link points to a directory rather than a file
        # typically errors like:
        # (urllib.error.HTTPError, IsADirectoryError, socket.timeout, urllib.error.URLError, ConnectionResetError)
        # extended to be indiscriminate since from the perspective of the full scrape, we probably don't care whether
        # we know about the error yet
        # TODO log error counts?
        except Exception as e:
            print('Failed to fetch:' + actual_image_link + ' due to: ' + str(type(e)))

    else:
        print('Skipped: '+actual_image_link)

driver = create_selenium_browser()

# build up a language-specific base link to start out with, before modifying it per each individual search term
# add on the hl field for all languages because if it is in our JSON file, it has a hl field
current_language_entry = full_language_arg_map[opts.language]
base_language_search_url = BASE_GOOGLE_IMAGE_SEARCH_LINK + '&hl=' + current_language_entry['hl']

# the lr field is present in some but not all of the language possibilities in the JSON config file
if len(current_language_entry['lr']) > 0:
    base_language_search_url += '&lr=' + current_language_entry['lr']

for word_index, foreign_word in enumerate(foreign_word_list):
    if VERBOSE_MOSE:
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('Current word: ' + foreign_word + ' at index: ' + str(word_index))
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    # if a start index was passed in, this is a case where we are resuming a previously failed run, skip every word
    # that successfully completed and just pick up where we left off
    if opts.start_index and word_index < opts.start_index: continue

    # retry search query up to 10 times if we hit failures
    for attempt in range(10):
        try:
            url = base_language_search_url + '&q=' + urllib.parse.quote(foreign_word)
            driver.get(url)
            time.sleep(2) #2 is arbitrary

            link_elements = driver.find_elements_by_xpath(GOOGLE_IMAGE_LINK_XPATH)

        # catch what seem to be BadStatusLine and ConnectionRefusedError's, quit the webdriver, and then create a new
        # instance. there is something really funky going on here that seems to work when resetting selenium
        except Exception as e:
            driver.quit()
            driver.stop_client()
            driver = create_selenium_browser()
            print('Search query failed for:' + url + ' due to: ' + str(type(e)) + ' retry:'+str(attempt))
        # break for loop on success
        else: break

    for link_element in link_elements:
        actual_image_link = get_image_link(link_element)

        # when in debug mode, just print the link out, otherwise download the file
        if DEBUG_MODE:
            print(actual_image_link)
        else:
            download_image(actual_image_link, word_index)

    # exit after first word in debug mode
    if DEBUG_MODE: exit()


