AMI used: ubuntu-trusty-14.04-amd64-server-20160114.5 (ami-fce3c696)
Instance size: t2.micro

1. Install python virtualenv: sudo apt-get install python-virtualenv
2. Install other dependencies: sudo apt-get install libxslt-dev libxml2-dev python-dev python3-dev zlib1g-dev git unzip
3. For lxml dependency, may need to install: sudo easy_install lxml
5. virtualenv --python python3 env
6. source env/bin/activate
7. pip install GoogleScraper chromedriver
8. Pull down google key: wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
9. Set the repo: sudo sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
10. Update the apt-get listings with new repo: sudo apt-get update
11. Install chrome: sudo apt-get install google-chrome-stable
12. Install xvfb for headless support: sudo apt-get install xvfb
13. Manually install latest chromedriver (might want to check link for newer version)
wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver

sudo mv -f chromedriver /usr/local/share/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver
14. Install latest firefox: sudo apt-get install firefox
15. Run xvfb in screen: 
screen -S xvfb
sudo Xvfb :10 -ac
detach: ctrl A-D
16. Set env var: export DISPLAY=:10
17. Install AWS SDK: pip install boto3
18. Create a ~/.boto config file with the following contents:
[Credentials]
aws_access_key_id = YOURACCESSKEY
aws_secret_access_key = YOURSECRETKEY
19. Install beaker library: pip install beaker
20. Install AWS command line tools: pip install awscli

