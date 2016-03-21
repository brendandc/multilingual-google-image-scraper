3. For lxml dependency, may need to install: sudo easy_install lxml
7. pip install GoogleScraper chromedriver
8. Pull down google key: wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
9. Set the repo: sudo sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
10. Update the apt-get listings with new repo: sudo apt-get update
11. Install chrome: sudo apt-get install google-chrome-stable
13. Manually install latest chromedriver (might want to check link for newer version)
wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
sudo mv -f chromedriver /usr/local/share/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver
17. Install AWS SDK: pip install boto3