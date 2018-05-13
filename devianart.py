#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread, Lock
import collections
import datetime
import time
import os
import pathlib
import requests
import subprocess

#======================== INITIALIZE VARIABLES =================================

images  = []
img_num = 0
workers = 20
threads = []
tasks   = Queue()
lock    = Lock()

#======================== WELCOME MESSAGE ======================================

def welcome_message():
    now = datetime.datetime.now()
    today = now.strftime("%A • %B %e • %H:%M • %Y")
    print('\n  DeviantArt Scraper')
    print('\n  DATE:  ' + today)

#======================== GET SELENIUM DRIVER ==================================

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    return driver

#======================== GET USERNAME =========================================

def get_username(d):
    global username
    html = d.page_source
    soup = BeautifulSoup(html, 'html.parser')
    username = soup.find(class_='gruserbadge').find('a').get_text()

#======================== GET LINKS FROM TUMBNAILS =============================

def get_thumb_links(q):
    d = get_driver()
    # REPLACE username with your preferred artist
    d.get('https://username.deviantart.com/gallery/')
    unique_img = scroll_page_down(d)
    time.sleep(0.5)
    for img in unique_img:
        q.put(img)
    global expected_img_num
    expected_img_num = str(len(unique_img))
    get_username(d)
    print('  Unique images found = ' + expected_img_num)
    print('  Artist = ' + username + "\n")
    time.sleep(0.5)
    d.close()

#======================== SCROLL DOWN ==========================================

def scroll_page_down(d):
    SCROLL_PAUSE_TIME = 1.5
    # Get scroll height
    last_height = d.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME) # Wait to load page
        # Calculate new scroll height and compare with last scroll height
        new_height = d.execute_script("return document.body.scrollHeight")
        # Get the tumbnail image links
        im = d.find_element_by_class_name('folderview-art')
        links = im.find_elements_by_class_name('torpedo-thumb-link')
        for link in links:
            l = link.get_attribute('href')
            images.append(l)
        unique_img = list(set(images)) # Remove duplicates
        time.sleep(0.5)
        # Break when the end is reached
        if new_height == last_height:
            break
        last_height = new_height
    return unique_img

#======================== GET FULL RESOLUTION IMAGES ===========================

def get_full_image(l):
    s = requests.Session()
    h = {'User-Agent': 'Firefox'}
    soup = BeautifulSoup(s.get(l, headers=h).text, 'html.parser')
    title = ''
    link = ''
    try:
        link = soup.find('a', class_='dev-page-download')['href']
    except TypeError:
        try:
            link = soup.find('img', class_='dev-content-full')['src']
            title = soup.find('a',
                                 class_='title').text.replace(' ', '_').lower()
        except TypeError:
            try:
                link = age_restricted(l)
            except (WebDriverException, AttributeError):
                link = age_restricted(l)
        pass
    req = s.get(link, headers=h)
    time.sleep(0.1)
    download_now(req,title)
    url = req.url
    ITuple = collections.namedtuple('ITuple', ['u', 't'])
    it = ITuple(u=url, t=title)
    return it

#======================== GET AGE-RESTRICTED IMAGES ============================

def age_restricted(l):
    d = get_driver()
    d.get(l)
    time.sleep(0.8)
    d.find_element_by_class_name('datefields')
    d.find_elements_by_class_name('datefield')
    d.find_element_by_id('month').send_keys('01')
    d.find_element_by_id('day').send_keys('01')
    d.find_element_by_id('year').send_keys('1991')
    d.find_element_by_class_name('tos-label').click()
    d.find_element_by_class_name('submitbutton').click()
    time.sleep(1)
    img_lnk = d.find_element_by_class_name('dev-page-download')
    d.get(img_lnk.get_attribute('href'))
    time.sleep(0.5)
    link = d.current_url
    d.close()
    return link

#======================== FILENAME FORMATTING ==================================

def name_format(url,title):
    if url.find('/'):
        name =  url.rsplit('/', 1)[1]
        p1 = name.split('-')[0]
        p2 = name.split('-')[1].split('.')[1]
        name = p1 + '.' + p2
    if title != '':
        name = title + '.png'
    return name

#======================== DOWNLOAD USING REQUESTS ==============================

def download_now(req,title):
    url = req.url
    name = name_format(url,title)
    pathlib.Path('{}.deviantart.com'.format(username)).mkdir(parents=True,
                                                             exist_ok=True)
    with open(os.path.join('{}.deviantart.com/'.format(username),
                                               '{}'.format(name)),'wb') as file:
        file.write(req.content)

#======================== SAVE IMAGE LINKS TO A FILE ===========================

def save_img(url):
    try:
        with open('{}-gallery.txt'.format(username), 'a+') as file:
            file.write(url + '\n')
    except:
        print('An write error occurred.')
        pass

#======================== WORKER THREAD ========================================

def worker_thread(q, lock):
    while True:
        link = q.get()
        if link is None:
            break
        p = get_full_image(link)
        url = p.u
        title = p.t
        name = name_format(url, title)
        with lock:
            global img_num
            img_num += 1
            save_img(url)
            print('Image ' + str(img_num) + ' - ' + name)
        q.task_done()

#======================== MAIN FUNCTION ========================================

def main():
    welcome_message() # Display Welcome Message
    start = time.time()
    get_thumb_links(tasks) # Fill the Queue

    # Start the Threads
    for i in range(workers):
         t = Thread(target = worker_thread, args = (tasks, lock))
         t.start()
         threads.append(t)

    # When done close worker threads
    tasks.join()
    for _ in range(workers):
        tasks.put(None)
    for t in threads:
        t.join()

    # Print Stats
    folder_size = subprocess.check_output(['du','-shx',
             '{}.deviantart.com/'.format(username)]).split()[0].decode('utf-8')
    print('\n  Total Images: ' + str(img_num) + ' (' + str(folder_size) + ')')
    print('  Excepted: ' + expected_img_num)
    end = time.time()
    print('  Elapsed Time: {:.4f}\n'.format(end-start))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
#===============================================================================