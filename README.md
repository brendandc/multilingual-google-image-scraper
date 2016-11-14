# Running the scraper

Assuming you've followed the steps for system setup, the steps I used to test the scraper are as follows:

1. Run xvfb in screen:

        screen -S xvfb
        sudo Xvfb :10 -ac
        
Then detach using: ctrl-A-D

2. Start screen session for scraping:

        screen -S scrape
        
3. Start scraping:

        python scrape-images.py -v -l language -d dictionaries/dictfile
        
Then detach using: ctrl-A-D
        
See `google-languages.json` for a list of supported language

# System setup

This code was developed and tested on an Ubuntu system running on AWS. The code was written and tested in Python 3, it will not work in Python 2 out of the box.

## Ubuntu setup

1. Make sure aptitude's listings are up to date: 

        sudo apt-get update
2. Install various dependencies, including virtualenv, xvfb, firefox: 

        sudo apt-get install python-virtualenv libxslt-dev libxml2-dev python-dev python3-dev zlib1g-dev git unzip xvfb firefox
3. Create a new python 3 virtualenv: 

        virtualenv --python python3 env
4. Append the following lines to the end of `~/.bashrc` for using virtualenv and xvfb: 

        source env/bin/activate
        export DISPLAY=:10
        
5. Install geckodriver wrapper for firefox
For newer versions of firefox, it is necessary to download and extract the latest version of [geckodriver](https://github.com/mozilla/geckodriver/releases).
Once downloaded, you'll need to add the directory where you extracted it to your path by adding a line to your `~/.bashrc` like:

        export PATH="/home/ubuntu/geckodriver:$PATH"
6. Logout/log back in or do 

        source ~/.bashrc
7. Install the python library requirements: 

        pip install -r requirements.txt
        
8. Clone the git repository with the latest code
        
        git clone git@github.com:brendandc/dictionary-based-google-image-scraper.git
    
## AWS setup

On AWS, I tested the code with a custom AMI that was extended from `ubuntu-trusty-14.04-amd64-server-20160114.5` and had only the steps in the Ubuntu setup section run on it.
As for system size, it was tested on `t2.micro` instances.

### Storage setup

I've listed out some helper commands if spinning up and attaching volumes to the AWS instance via the console for scraping and packaging respectively.

#### Scraping

        sudo mkdir /mnt/storage
        sudo mkfs -t ext4 /dev/xvdf
        sudo mount /dev/xvdf /mnt/storage
        sudo chown ubuntu:ubuntu /mnt/storage

#### Packaging

        sudo mkdir /mnt/storage2
        sudo mkfs -t ext4 /dev/xvdg
        sudo mount /dev/xvdg /mnt/storage2
        sudo chown ubuntu:ubuntu /mnt/storage2
        
### S3 setup

For uploading to s3, create a ~/.boto config file with the following contents:

        [Credentials]
        aws_access_key_id = YOURACCESSKEY
        aws_secret_access_key = YOURSECRETKEY
        
#### Useful commands

Get bucket size in bytes:

        aws s3api list-objects --bucket brendan.callahan.thesis --output json --query "[sum(Contents[].Size), length(Contents[])]"
        
Get full listing with prefix:

        aws s3api list-objects --bucket brendan.callahan.thesis --prefix 'packages/' --output json

# Packaging results

        python create-language-zip.py -l English
        
Note: this script is hard-coded to use the directories under AWS storage setup, and upload automatically to S3

# Extracting existing package

        python extract_language_package -f filename.tar -d destination_dir -l language
        
# Get package report summary details

        python report-package.py -d extracted_package_dir -o output_file.json
        
# Dictionaries

The dictionaries folder includes a set of dictionaries originally generated for the paper: [The Language Demographics of Amazon Mechanical Turk](http://www.seas.upenn.edu/~epavlick/papers/language_demographics_mturk.pdf)
which was was written by Ellie Pavlick, Matt Post, Ann Irvine, Dmitry Kachaev, Chris Callision-Burch. TACL 2014.

I made a few minor additions to the set of dictionaries. Any dictionary with one search term/phrase per line will work with `scrape-images.py`. 

# Auxiliary data files

## google-languages.json
This file was created from the following reference: [Google language codes](https://sites.google.com/site/tomihasa/google-language-codes)

In PyCharm, I used the following regex to jsonify the copy/pasted page contents.
search: hl=([\w-]+)\s+([\p{L}\(\) -]+)
replace: "$2":{"hl":"$1", "lr":""},

## user_agents.json
I found a list of most commonly used user-agent headers online and manually created a json file with those string values.
