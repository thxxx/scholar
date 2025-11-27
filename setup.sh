sudo apt-get update
sudo apt-get install -y ffmpeg
sudo apt-get install -y python3-pip unzip wget
sudo apt-get install xvfb google-chrome-stable
pip install tqdm pandas selenium requests selenium-stealth
# pip install tqdm pandas selenium requests google-cloud-storage blinker==1.4.0 selenium-wire --break-system-packages
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f
# sudo apt-get -f install -y
# CHROME_DRIVER_VERSION=$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
# wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/142.0.7444.175/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver