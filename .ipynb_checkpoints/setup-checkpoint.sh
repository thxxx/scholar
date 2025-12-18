apt-get update
apt-get install -y ffmpeg
apt-get install -y vim
apt-get install -y python3-pip unzip wget
apt-get install -y xvfb google-chrome-stable

git config user.email zxcv05999@naver.com
git config user.name thxxx

python3 -m pip install tqdm pandas selenium requests selenium-stealth beautifulsoup4 openai
# pip install tqdm pandas selenium requests google-cloud-storage blinker==1.4.0 selenium-wire --break-system-packages
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb
apt-get install -f -y
# sudo apt-get -f install -y
# CHROME_DRIVER_VERSION=$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
# wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/142.0.7444.175/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
