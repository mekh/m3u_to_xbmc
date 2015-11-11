#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import urllib2
from urllib import urlretrieve
from BeautifulSoup import BeautifulSoup

url = 'http://sunline.net.ua/iptv.html'
icons_dir = 'icons'


def decode_base64(image, name, ico_dir):
    img = re.compile('.*base64,(.*)$').match(image).group(1)
    ext = re.compile('.*image/(.*);base64.*').match(image).group(1)
    name = os.path.join(ico_dir, '{0}.{1}'.format(name.encode('utf-8'), ext))
    print "Decoding file: " + name
    with open(name, 'wb') as image_file:
        image_file.write(img.decode('base64'))


def download_img(address, name, ico_dir):
    ext = re.compile('.*\.([^\.]*)$').match(address).group(1)
    name = os.path.join(ico_dir, '{0}.{1}'.format(name.encode('utf-8'), ext))
    print "Fetching file: " + name
    urlretrieve(address, name)


def parse_page(ico_url, ico_dir):
    page = urllib2.urlopen(ico_url)
    soup = BeautifulSoup(page.read())
    for item in soup.findAll("div", {"style": "clear:both;padding:5px;"}):
        for div in item.findAll("div"):
            img = div.find("img")["src"]
            name = div.find("img")["alt"]
            if re.match('data:image', img):
                decode_base64(img, name, ico_dir)
            else:
                download_img(img, name, ico_dir)


def main():
    if os.path.exists(icons_dir) is False:
        os.mkdir(icons_dir)
    parse_page(url, icons_dir)


if __name__ == '__main__':
    main()
