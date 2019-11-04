import time
import os
import re
import urllib.request
from urllib.parse import urlparse
import shutil
import json
import optparse
import random
from collections import defaultdict
import traceback
import threading
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from selenium.webdriver.common.keys import Keys

from selenium import webdriver

# tbm=isch sets this to be image search, start=0 will give us 100 results on page 1
BASE_GOOGLE_IMAGE_SEARCH_LINK = 'https://www.google.com/search?#tbm=isch&start=0'

# regex for extracting source link component: http://www.inddist.com/sites/inddist.com/files/Dollar-Sign.jpg
# from compound links like:
# https://www.google.com/imgres?imgurl=http://www.inddist.com/sites/inddist.com/files/Dollar-Sign.jpg&imgrefurl=http://www.inddist.com/article/2015/05/put-dollar-sign-next-your-service-value&h=1600&w=1200&tbnid=9XAphqXNraTVnM:&docid=Hm9c-cTh-Hl_DM&ei=43-xVsTKMsixeNrCoNAL&tbm=isch&ved=0ahUKEwiEyMjt3trKAhXIGB4KHVohCLoQMwgdKAAwAA
IMAGE_URL_REGEX = r'imgres\?imgurl=(?P<url>.*?)(&imgrefurl)'

# XPATH statement that finds all of the links on the page that correspond to the original image links
# Note: this is probably subject to change on google's part
GOOGLE_IMAGE_LINK_XPATH = "//a[@class='rg_l']"

# XPATH statement that pulls the div adjacent to the image link path that contains google-created metadata
# Note: this is probably subject to change on google's part
GOOGLE_METADATA_XPATH = "//div[@class='rg_meta notranslate']"

# List of Valid file extensions to check against, if any of these don't match, this means our regex didn't quite
# parse the link correctly to pull out the real file link.
# Note: check for presence in list is also lowercased
VALID_FILE_EXTENSIONS = ['jpg', 'jpeg', 'gif', 'png', 'ico', 'bmp', 'svg']

# 6x gives us a decent boost in speed, and should hopefully offset some of the delays via sleeps
threadLimiter = threading.BoundedSemaphore(6)

# lock for printing to console
printing_lock = threading.Lock()

# create an in memory cache for storing hostnames, so that we can throttle requests on recently seen
# hostnames, to avoid potentially getting flagged for flooding servers. 15 seconds seems a reasonable amount of time
# to make sure we throttle on
cache_manager = CacheManager(**parse_cache_config_options({'cache.type': 'memory'}))
hostname_cache = cache_manager.get_cache('hostnames', type='memory', expire=15)

DEBUG_MODE = False


# defines the downloader threads so that we can download images in a concurrent way
class DownloadThread(threading.Thread):
    def __init__(self, word_downloader, href_attribute, link_index, current_metadata, base_path_for_word, user_agent, verbose_mode):
        self.word_downloader = word_downloader
        self.href_attribute = href_attribute
        self.link_index = link_index
        self.current_metadata = current_metadata
        self.base_path_for_word = base_path_for_word
        self.user_agent = user_agent
        self.verbose_mode = verbose_mode
        threading.Thread.__init__(self)

    # simple wrapper function for thread safe console printing,
    # so we can wrap all of our multi-threaded console output in one function
    def thread_safe_print(self, output):
        with printing_lock:
            print(output)

    # takes the link element from xpath, dissects out the href attribute, and runs a regex to extract the source URL
    def get_image_link(self, href_attribute):
        # some links are double or triple quoted, by chaining this call 3 times, we seem to unquote most of it
        # there is no functional downside that i know of for unquoting more than need be
        triple_decoded_attr = urllib.parse.unquote(urllib.parse.unquote(urllib.parse.unquote(href_attribute)))
        regex_result = re.search(IMAGE_URL_REGEX, triple_decoded_attr)

        # short-circuit regex error to return href - it will still fail, but without knocking over the thread
        if regex_result is None:
            return href_attribute

        return regex_result.group('url')

    def run(self):
        threadLimiter.acquire()
        try:
            # take the list href attribute, and extract the actual image link from that compound string
            actual_image_link = self.get_image_link(self.href_attribute)

            # force the link index string to be two digits (like 01, 02, etc), and then store the
            link_index_str = "{0:0=2d}".format(self.link_index+1)

            # take the metadata stored in an adjacent div as JSON, load it as a hash, and add it to our metadata
            google_metadata_for_image = json.loads(self.current_metadata)

            metadata_for_image = {'image_link': actual_image_link, 'google': google_metadata_for_image}

            # extract the actual file name and the file extension
            actual_file_name = actual_image_link.split('/')[-1]
            metadata_for_image['original_filename'] = actual_file_name
            file_extension = actual_file_name.split('.')[-1]
            no_extension = False

            # ggpht images seem to be internal to the search engine results, skipping them
            if actual_image_link.find('ggpht.com/') != -1:
                self.thread_safe_print('Skipped ggpht link: ' + actual_image_link)
                metadata_for_image['skipped'] = True
            else:
                # extract the net location from the link, like www.google.com, www.yahoo.com, etc
                net_location = urlparse(actual_image_link).netloc

                # check if the current net location is in the cache, if it is in the cache, then sleep for a short
                # amount of time. 3 seconds is an arbitrary choice but it should slow things down enough for the sake
                # of external servers without dragging all downloads to a halt
                #
                # n.b. this is not intended to achieve mutual exclusivity for any one hostname, only to track which
                # ones we've recently requested from and slow them down a little bit. fwiw: i don't think limiting
                # requests for any given host to one thread is desirable, since multiple requests are frequently made
                # when browsing to websites where such images are hosted anyways.
                try:
                    hostname_cache.get(net_location)
                    time.sleep(3)
                    if DEBUG_MODE:
                        self.thread_safe_print('hit:'+net_location)
                except KeyError:
                    if DEBUG_MODE:
                        self.thread_safe_print('miss:'+net_location)

                # if the file path does not have a valid extension, mark this as such so that we can set it later
                # based on the actual content type (which typically falls in our allowed list)
                if not file_extension.lower() in VALID_FILE_EXTENSIONS:
                    return
                    #no_extension = True

                # when in debug mode, just print the link out, otherwise download the file
                if DEBUG_MODE:
                    self.thread_safe_print(actual_image_link)
                else:
                    # make sure we re-quote the link for the sake of any special characters.
                    # Note: we need to skip the :/ for the http:// and the uri component separators, the ?&= for
                    # query arguments, and the comma also blows up on us
                    quoted_image_link = urllib.parse.quote(actual_image_link, ':/,?&=')

                    if self.verbose_mode: self.thread_safe_print('Downloading... ' + quoted_image_link)

                    metadata_for_image['filename'] = link_index_str+'.'+file_extension

                    # get the full path where we will store the image, e.g. base_path/01.jpg
                    full_path = self.base_path_for_word+metadata_for_image['filename']

                    try:
                        # Crucial, fudge the user-agent string here so that network admins don't think we are
                        # urllib, since anything "programmatic" is automatically conflated with an "attack"
                        # quote for the sake of special characters
                        request = urllib.request.Request(quoted_image_link, None, {
                            'User-Agent': self.user_agent
                        })
                        with urllib.request.urlopen(request, timeout=30) as response, open(full_path, 'wb') as out_file:
                            content_type = response.info().get_content_type()
                            shutil.copyfileobj(response, out_file)

                        # if there was no file extension and this is a content-type of image,
                        # lets use the content-type from the request to set it, [6:] takes everything after image/
                        # note: with the 1-liner above for the file path, it seems we need this workaround
                        # TODO: should probably deconstruct it
                        if no_extension and content_type.startswith('image/'):
                            original_file_path = full_path
                            new_file_path = self.base_path_for_word + link_index_str + '.' + content_type[6:]
                            shutil.move(original_file_path, new_file_path)

                        metadata_for_image['success'] = True

                    # catch some 503/504 type errors and also if the link points to a directory rather than a file
                    # typically errors like:
                    # (urllib.error.HTTPError, IsADirectoryError, socket.timeout, urllib.error.URLError, ConnectionResetError)
                    # extended to be indiscriminate since from the perspective of the full scrape, we probably don't care whether
                    # we know about the error yet
                    # TODO log error counts?
                    except Exception as e:
                        error_class = type(e).__name__
                        self.word_downloader.increment_error_count_for_class(error_class)
                        metadata_for_image['success'] = False
                        metadata_for_image['error_class'] = error_class
                        self.thread_safe_print('Failed to fetch:' + quoted_image_link + ' due to: ' + error_class +
                                               ' unquoted:' + actual_image_link)
                        if DEBUG_MODE: self.thread_safe_print(traceback.format_exc())

                self.word_downloader.add_metadata_for_word_index(link_index_str, metadata_for_image)
                hostname_cache.put(net_location, True)

        finally:
            threadLimiter.release()

class WordImageDownloader:
    def __init__(self, scraper, word, word_index, href_attributes, metadatas, verbose_mode):
        self.scraper = scraper
        self.word = word
        self.word_index = word_index
        self.href_attributes = href_attributes
        self.metadatas = metadatas
        self.verbose_mode = verbose_mode

        # track a dictionary with the errors for the current words
        self.current_word_download_errors = defaultdict(int)

        # use /base_path/language/word_index for storing words
        self.base_path_for_word = scraper.base_image_language_path+'/'+str(self.word_index)+'/'

        # ensure directory is created for this word index
        if not os.path.exists(self.base_path_for_word): os.makedirs(self.base_path_for_word)

        # hash to store the metadata information for each image we download, keyed by the word index
        self.image_metadata_for_word = {}

        # lock to ensure thread safe incrementing of error classes within error class count tracking hashes
        self.error_hash_lock = threading.Lock()

        # lock to ensure thread safe updating of the metadata hash for all the images for this word
        self.image_metadata_lock = threading.Lock()

    # function that updates the count of this error for the word, and for all words
    def increment_error_count_for_class(self, error_class):
        with self.error_hash_lock:
            self.current_word_download_errors[error_class] += 1
            self.scraper.increment_error_count_for_class(error_class)

    # function that updates the metadata, given a link index and metadata payload.
    # extra cautious with a lock in case anything might go wrong thread-safety wise
    def add_metadata_for_word_index(self, link_index_str, metadata):
        with self.image_metadata_lock:
            self.image_metadata_for_word[link_index_str] = metadata

    # main function that drives processing the current word, creates a bunch of download threads and then fires
    # them off
    def process_word(self):
        thread_list = []
        for link_index, href_attribute in enumerate(self.href_attributes):
            current_metadata = self.metadatas[link_index]
            user_agent = self.scraper.get_random_user_agent()
            current_thread = DownloadThread(self, href_attribute, link_index, current_metadata,
                                            self.base_path_for_word, user_agent, self.verbose_mode)
            thread_list.append(current_thread)

        for t in thread_list[0:100]:
            if (len(os.listdir(self.base_path_for_word)) < 100):
                t.start()

        for t in thread_list[0:100]:
            t.join()
        if (len(os.listdir(self.base_path_for_word)) < 100):
            i = 100
            while (len(os.listdir(self.base_path_for_word)) < 100):
                 thread_list[i].start()
                 thread_list[i].join()
                 i+=1
                 print(i)

        # dump out the json metadata and errors files
        json.dump(self.image_metadata_for_word, open(self.base_path_for_word+'metadata.json', 'w', encoding='utf-8'))
        json.dump(self.current_word_download_errors, open(self.base_path_for_word+'errors.json', 'w', encoding='utf-8'))

        # write out a simple text file that contains the word itself on one line in the same directory
        with open(self.base_path_for_word+'word.txt', 'w', encoding='utf-8') as text_file:
            text_file.write(self.word)

        # exit after first word in debug mode
        if DEBUG_MODE:
            # sleep 10 seconds between google searches in debug mode to prevent hammering
            time.sleep(5)

            # arbitrary testing point of 100 iterations before exiting in debug mode
            if self.word_index > 100: exit()

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
        self.base_language_search_url = BASE_GOOGLE_IMAGE_SEARCH_LINK

        # if a domain suffix was provided, swap out google.com for google.(domain)
        if opts.domain_suffix is not None:
            self.base_language_search_url = self.base_language_search_url.replace("google.com",
                                                                                  "google."+opts.domain_suffix)

        # if there are any language bindings in our google languages map for this language, pass those flags along
        # otherwise, we'll use the default settings
        if opts.language in full_language_arg_map:
            current_language_entry = full_language_arg_map[opts.language]

            # add on the hl field for all languages because if it is in our JSON file, it has a hl field
            self.base_language_search_url += '&hl=' + current_language_entry['hl']

            # the lr field is present in some but not all of the language possibilities in the JSON config file
            if len(current_language_entry['lr']) > 0:
                self.base_language_search_url += '&lr=' + current_language_entry['lr']

        # parse a json file with common user-agent strings to customize, file was manually generated
        with open(opts.user_agent_list, encoding='utf-8') as data_file:
            self.user_agent_list = json.loads(data_file.read())

        # extract the base image path
        base_image_path = opts.base_image_path
        if not base_image_path.endswith("/"):
            base_image_path += "/"

        # create the combined base image language path
        self.base_image_language_path = base_image_path + opts.language

        # provides extra debug output when configured
        self.verbose_mode = opts.verbose_mode

        # simple re-mapping barring better resolution
        self.opts = opts

    # accessor method for incrementing the count of errors for a class
    def increment_error_count_for_class(self, error_class):
        self.all_word_download_errors[error_class] += 1

    # simple function to grab a random user agent
    def get_random_user_agent(self):
        return random.choice(self.user_agent_list)

    # creates a selenium browser instance with Firefox
    def create_selenium_browser(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)#10 is arbitrary

    # get the href attributes that contain the underlying image links
    def get_href_attributes_for_word(self, word):
        # initialize an array of href attributes and metadatas that are extracted via selenium
        href_attributes = []
        google_metadatas = []

        # create the search url for this word by appending the search term onto our base search URL for the language
        # quote for the sake of special characters
        url = self.base_language_search_url + '&q=' + urllib.parse.quote(word)

        # retry search query up to 10 times if we hit failures
        # deliberately encapsulates all of the interaction with the selenium library in this retry loop and
        # try/except blocks so that we can handle selenium library errors in a common way
        for attempt in range(10):
            try:
                self.driver.get(url)
                self.driver.execute_script("window.scrollBy(0, 1000000);")
                time.sleep(2) #2 is arbitrary

                # pull all elements out of the page using the google-specific xpath for the elements that contain
                # the underlying image links
                link_elements = self.driver.find_elements_by_xpath(GOOGLE_IMAGE_LINK_XPATH)
                #print(self.driver.find_elements_by_xpath("//div[@class='rg_meta notranslate']"))

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
        if self.opts.skip_completed_words:
            print('skip_completed_words selected, only downloading for words that have no images')

        for word_index, foreign_word in enumerate(self.foreign_word_list):
            # if a start index was passed in, this is a case where we are resuming a previously failed run, skip every word
            # that successfully completed and just pick up where we left off
            if self.opts.start_index and word_index < self.opts.start_index: continue

            # if the skip_completed_words option was provided, we want to:
            # check if we have downloaded any images for this word, and skip this word if so
            # the idea being that we are just trying to fill in any words where something failed and we did not
            # download anything
            if self.opts.skip_completed_words:
                path_for_word = self.base_image_language_path+'/'+str(word_index)
                if os.path.exists(path_for_word):
                    num_files = len(os.listdir(path_for_word))
                else:
                    num_files = 0

                # if there are more than 3 files (word.txt, errors.json, metadata.json), we can more or less safely
                # assume this was a successful run. if only 3 files then we want to re-download images for this word
                if num_files > 3:
                    continue

            if self.verbose_mode:
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                print('Current word: ' + foreign_word + ' at index: ' + str(word_index))
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

            href_attributes, metadatas = self.get_href_attributes_for_word(foreign_word)

            word_image_downloader = WordImageDownloader(self, foreign_word, word_index, href_attributes, metadatas,
                                                        self.verbose_mode)
            word_image_downloader.process_word()
            

        if not self.opts.skip_completed_words:
            json.dump(self.all_word_download_errors, open(self.base_image_language_path+'/all_errors.json', 'w', encoding='utf-8'))

def main(opts):
    # initialize the image scraper class with the comand line options, then process all the words
    image_scraper = GoogleImageScraper(opts)
    image_scraper.process_all_words()

if __name__ == '__main__':
    optparser = optparse.OptionParser()
    optparser.add_option("-l", "--language", dest="language", default="French", help="Language to scrape")
    optparser.add_option("-n", "--num_images", dest="num_images", default=100, type=int,
                         help="Number of images to harvest per word")
    optparser.add_option("-d", "--dictionary", dest="dictionary", default="dictionaries/dict.fr",
                         help="Google languages json file")
    optparser.add_option("-L", "--language-map", dest="language_map", default="google-languages.json",
                         help="Google languages json file")
    optparser.add_option("-s", "--start-index", dest="start_index", default=None, type=int,
                         help="Word index to start iterating at")
    optparser.add_option("-p", "--base-image-path", dest="base_image_path", default='/mnt/storage/',
                         help="Base path where to store image output")
    optparser.add_option("-u", "--user-agent-list", dest="user_agent_list", default='user_agents.json',
                         help="JSON file with an array of user agents to randomly select from")
    optparser.add_option("-v", action="store_true", dest="verbose_mode", help="Verbose mode")
    optparser.add_option("-S", action="store_true", dest="skip_completed_words",
                         help="Allows multiple passes on a dictionary file so that we can fetch images for any words that failed to get any")
    optparser.add_option("-D", "--domain-suffix", dest="domain_suffix",
                         help="Allow switching the domain suffix (i.e. google.com vs google.fr)")
    (opts, _) = optparser.parse_args()

    main(opts)
