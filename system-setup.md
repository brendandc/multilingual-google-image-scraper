AMI used: ubuntu-trusty-14.04-amd64-server-20160114.5 (ami-fce3c696)
Instance size: t2.micro

1. sudo apt-get update
2. Install python virtualenv: sudo apt-get install python-virtualenv
3. Install other dependencies: sudo apt-get install libxslt-dev libxml2-dev python-dev python3-dev zlib1g-dev git unzip
4. Install xvfb for headless support: sudo apt-get install xvfb
5. Install latest firefox: sudo apt-get install firefox
6. virtualenv --python python3 env
7. For python3 virtualenv and xvfb/firefox connection, add the following lines to the end of ~/.bashrc: 
source env/bin/activate
export DISPLAY=:10
8. Logout/log back in or do source ~/.bashrc
9. Install beaker library: pip install beaker
10. Install AWS command line tools: pip install awscli
11. Install selenium library: pip install selenium
12. (Post-processing only) Create a ~/.boto config file with the following contents:
[Credentials]
aws_access_key_id = YOURACCESSKEY
aws_secret_access_key = YOURSECRETKEY
13. Run xvfb in screen: 
screen -S xvfb
sudo Xvfb :10 -ac
detach: ctrl A-D
14. Setup hard drive for downloading to
sudo mkdir /mnt/storage
sudo mkfs -t ext4 /dev/xvdf
sudo mount /dev/xvdf /mnt/storage
sudo chown ubuntu:ubuntu /mnt/storage
15. (Post-processing only) Setup hard drive for packaging to
mkdir /mnt/storage2
sudo mount /dev/xvdg /mnt/storage2
sudo chown ubuntu:ubuntu /mnt/storage2
16. In homedir, clone our repo: git clone git@github.com:brendandc/image-scraper.git
17. Start screen session for scraping from homedir: screen -S scrape
18. Start scraping with: python scrape-images.py -v -l language -d dictionaries/dictfile
