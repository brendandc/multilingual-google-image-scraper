import time
import os
import re
import urllib.request
import shutil
import json
import optparse
from collections import defaultdict
import boto3
import socket

from selenium import webdriver

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to scrape")
optparser.add_option("-n", "--num_images", dest="num_images", default=100, type=int, help="Number of images to harvest per word")
optparser.add_option("-d", "--dictionary", dest="dictionary", default="dict.fr", help="Google languages json file")
optparser.add_option("-L", "--language-map", dest="language_map", default="google-languages.json", help="Google languages json file")
optparser.add_option("-s", "--start-index", dest="start_index", default=None, type=int, help="Word index to start iterating at")
optparser.add_option("-p", "--base-image-path", dest="base_image_path", default='/mnt/storage/images/', help="Base path where to store image output")
optparser.add_option("-v", action="store_true", dest="verbose_mode", help="Verbose mode")
(opts, _) = optparser.parse_args()

# tbm=isch sets this to be image search, start=0 will give us 100 results on page 1
BASE_GOOGLE_IMAGE_SEARCH_LINK = 'https://www.google.com/search?#tbm=isch&start=0'

# regex for extracting source link component: http://www.inddist.com/sites/inddist.com/files/Dollar-Sign.jpg
# from compound links like:
# https://www.google.com/imgres?imgurl=http://www.inddist.com/sites/inddist.com/files/Dollar-Sign.jpg&imgrefurl=http://www.inddist.com/article/2015/05/put-dollar-sign-next-your-service-value&h=1600&w=1200&tbnid=9XAphqXNraTVnM:&docid=Hm9c-cTh-Hl_DM&ei=43-xVsTKMsixeNrCoNAL&tbm=isch&ved=0ahUKEwiEyMjt3trKAhXIGB4KHVohCLoQMwgdKAAwAA
IMAGE_URL_REGEX = r'imgres\?imgurl=(?P<url>.*?)&'

# XPATH statement that finds all of the links on the page that correspond to the original image links
# Note: this is probably subject to change on google's part
GOOGLE_IMAGE_LINK_XPATH = "//a[@class='rg_l']"

# XPATH statement that pulls the div adjacent to the image link path that contains google-created metadata
# Note: this is probably subject to change on google's part
GOOGLE_METADATA_XPATH = "//div[@class='rg_meta']"

# user agent string from a recent version of firefox, override the default urllib User-Agent value
USER_AGENT_STRING = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0"

DEBUG_MODE = False

# class that handles image scraping in google
class GoogleImageScraper(object):
    def __init__(self, opts):
        # creates the driver for running selenium
        self.driver = None # dummy call to ensure instance var is created in init
        self.create_selenium_browser()

        # track a dictionary with the errors for all words
        self.all_word_download_errors = defaultdict(int)

        # read in the json file with the arguments (hl and lr) for each language in google
        with open(opts.language_map, encoding='utf-8') as data_file:
            full_language_arg_map = json.loads(data_file.read())

        # pull the foreign words out of the bilingual dictionary, this assumes the format foreign\tenglish\n
        self.foreign_word_list = [line.strip().split('\t')[0] for line in open(opts.dictionary)]

        # build up a language-specific base link to start out with, before modifying it per each individual search term
        # add on the hl field for all languages because if it is in our JSON file, it has a hl field
        current_language_entry = full_language_arg_map[opts.language]
        self.base_language_search_url = BASE_GOOGLE_IMAGE_SEARCH_LINK + '&hl=' + current_language_entry['hl']

        # the lr field is present in some but not all of the language possibilities in the JSON config file
        if len(current_language_entry['lr']) > 0:
            self.base_language_search_url += '&lr=' + current_language_entry['lr']


    # creates a selenium browser instance with Firefox
    def create_selenium_browser(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)#10 is arbitrary

    # takes the link element from xpath, dissects out the href attribute, and runs a regex to extract the source URL
    def get_image_link(self, href_attribute):
        regex_result = re.search(IMAGE_URL_REGEX, href_attribute)
        return regex_result.group('url')

    # get the href attributes that contain the underlying image links
    def get_href_attributes_for_word(self, word):
        # initialize an array of href attributes that are extracted via selenium
        href_attributes = []

        # create the search url for this word by appending the search term onto our base search URL for the language
        url = self.base_language_search_url + '&q=' + urllib.parse.quote(word)

        # retry search query up to 10 times if we hit failures
        # deliberately encapsulates all of the interaction with the selenium library in this retry loop and
        # try/except blocks so that we can handle selenium library errors in a common way
        for attempt in range(10):
            try:
                self.driver.get(url)
                time.sleep(2) #2 is arbitrary

                # pull all elements out of the page using the google-specific xpath for the elements that contain
                # the underlying image links
                link_elements = self.driver.find_elements_by_xpath(GOOGLE_IMAGE_LINK_XPATH)

                # also pull the google-created metadatas out of the page, stored as JSON in a hidden div
                google_metadatas = [s.get_attribute('innerHTML') for s in self.driver.find_elements_by_xpath(GOOGLE_METADATA_XPATH)]

                # pull the href attribute out of each element that contains the underlying image link
                # note: need to keep this inside the retries and try/except catch blocks.
                # there is an occasional selenium issue where even get_attribute can inexplicably fail
                # TODO for this occasional failure, we may have to add a timeout to all of the selenium code as a whole,
                # as it caused the scraper to hang endlessly
                href_attributes = [ link_element.get_attribute('href') for link_element in link_elements ]


            # catch what seem to be BadStatusLine and ConnectionRefusedError's, quit the webdriver, and then create a new
            # instance. there is something really funky going on here that seems to work when resetting selenium
            except Exception as e:
                self.driver.quit()
                self.driver.stop_client()
                self.create_selenium_browser()
                print('Search query failed for:' + url + ' due to: ' + type(e).__name__ + ' retry:'+str(attempt))
            # break for loop on success
            else: break

        return [href_attributes, google_metadatas]

    # function that drives processing every word in the parsed list of words
    def process_all_words(self):
        for word_index, foreign_word in enumerate(self.foreign_word_list):
            # if a start index was passed in, this is a case where we are resuming a previously failed run, skip every word
            # that successfully completed and just pick up where we left off
            if opts.start_index and word_index < opts.start_index: continue

            if opts.verbose_mode:
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                print('Current word: ' + foreign_word + ' at index: ' + str(word_index))
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

            # track a dictionary with the errors for the current words
            current_word_download_errors = defaultdict(int)

            base_path_for_index = opts.base_image_path+str(word_index)+'/'
            # ensure directory is created for this word index
            if not os.path.exists(base_path_for_index): os.makedirs(base_path_for_index)

            # array to store the metadata dictionaries for each image we download
            list_of_image_metadata = []

            href_attributes, metadatas = self.get_href_attributes_for_word(foreign_word)

            for link_index, href_attribute in enumerate(href_attributes):
                # take the list href attribute, and extract the actual image link from that compound string
                actual_image_link = self.get_image_link(href_attribute)

                # force the link index string to be two digits (like 01, 02, etc), and then store the
                link_index_str = "{0:0=2d}".format(link_index+1)

                # take the metadata stored in an adjacent div as JSON, load it as a hash, and add it to our metadata
                google_metadata_for_image = json.loads(metadatas[link_index])

                metadata_for_image = {'image_link': actual_image_link, 'google': google_metadata_for_image}

                # when in debug mode, just print the link out, otherwise download the file
                if DEBUG_MODE:
                    print(actual_image_link)
                else:
                    actual_file_name = actual_image_link.split('/')[-1]
                    metadata_for_image['original_filename'] = actual_file_name
                    file_extension = actual_file_name.split('.')[-1]

                    if opts.verbose_mode: print('Downloading... ' + actual_image_link)

                    # ggpht images seem to be internal to the search engine results, skipping them
                    if actual_image_link.find('ggpht.com/') == -1:
                        metadata_for_image['filename'] = link_index_str+'.'+file_extension

                        # get the full path where we will store the image, e.g. base_path/01.jpg
                        full_path = base_path_for_index+metadata_for_image['filename']

                        try:
                            # Crucial, fudge the user-agent string here so that network admins don't think we are
                            # urllib, since anything "programmatic" is automatically conflated with an "attack"
                            request = urllib.request.Request(actual_image_link, None, {
                                'User-agent' : USER_AGENT_STRING
                            })
                            with urllib.request.urlopen(request, timeout=30) as response, open(full_path, 'wb') as out_file:
                                shutil.copyfileobj(response, out_file)

                        # catch some 503/504 type errors and also if the link points to a directory rather than a file
                        # typically errors like:
                        # (urllib.error.HTTPError, IsADirectoryError, socket.timeout, urllib.error.URLError, ConnectionResetError)
                        # extended to be indiscriminate since from the perspective of the full scrape, we probably don't care whether
                        # we know about the error yet
                        # TODO log error counts?
                        except Exception as e:
                            error_class = type(e).__name__
                            self.all_word_download_errors[error_class] += 1
                            current_word_download_errors[error_class] += 1
                            print('Failed to fetch:' + actual_image_link + ' due to: ' + error_class)

                    else:
                        print('Skipped: '+actual_image_link)

                list_of_image_metadata.append(metadata_for_image)

            json.dump(list_of_image_metadata, open(base_path_for_index+'metadata.json', 'w'))
            json.dump(current_word_download_errors, open(base_path_for_index+'errors.json', 'w'))

            # exit after first word in debug mode
            if DEBUG_MODE: exit()

        json.dump(self.all_word_download_errors, open(opts.base_image_path+'all_errors.json', 'w'))


# initialize the image scraper class with the comand line options, then process all the words
image_scraper = GoogleImageScraper(opts)
image_scraper.process_all_words()


#  when S3 mode is turned on, upload the file over to S3 and delete the local copy
# TODO can we simplify this so it doesn't need to write out to a tmp location?
# TODO add metadata like original link to storage?
# S3_BUCKET_NAME = 'brendan.callahan'
# S3_BASE_PATH = 'thesis/images/'+opts.language+'/'
# if STORAGE_MODE == 'S3':
#     word_index_str = "{0:0=2d}".format(word_index)
#     destination_path = S3_BASE_PATH+word_index_str+'/'+actual_file_name
#     s3_client = boto3.resource('s3')
#     s3_client.meta.client.upload_file(full_path, S3_BUCKET_NAME, destination_path)
#     os.remove(full_path)
