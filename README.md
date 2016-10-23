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

This code was developed and tested on an Ubuntu system running on AWS. 

## Ubuntu setup

1. Make sure aptitude's listings are up to date: 

        sudo apt-get update
2. Install various dependencies, including virtualenv, xvfb, firefox: 

        sudo apt-get install python-virtualenv libxslt-dev libxml2-dev python-dev python3-dev zlib1g-dev git unzip xvfb firefox
3. Create a new python virtualenv: 

        virtualenv --python python3 env
4. Append the following lines to the end of `~/.bashrc` for using virtualenv and xvfb: 

        source env/bin/activate
        export DISPLAY=:10
5. Logout/log back in or do 

        source ~/.bashrc
6. Install the python library requirements: 

        pip install -r requirements.txt
        
7. Clone the git repository with the latest code
        
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
