# pip install --upgrade google-api-python-client

# script for using google's custom search engine to scrape images.. currently limited to 100 searches per day..

import pprint

from googleapiclient.discovery import build

API_KEY = 'AIzaSyBKBXFJ2QW4BEF96sAx03UTU9A-1T30n08'
SEARCH_ENGINE = '012938690586436426342:ql6tkoogagu'

def main():
    # Build a service object for interacting with the API. Visit
    # the Google APIs Console <http://code.google.com/apis/console>
    # to get an API key for your own application.
    service = build("customsearch", "v1", developerKey=API_KEY)

    res = service.cse().list(
            q='bernie',
            searchType='image',
            cx=SEARCH_ENGINE,
    ).execute()
    pprint.pprint(res)


if __name__ == '__main__':
    main()
