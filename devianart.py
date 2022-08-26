#!/usr/bin/env python3
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
import imghdr
import argparse
from random import randint
from chromedriver import get_driver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

#======================== INITIALIZE VARIABLES =================================

images  = []
workers = 1 #20
threads = []
tasks   = Queue()
lock    = Lock()
img_num = 0
max_image_count = 0 # Set to 0 for all images.
no_image_found_count = 0
folder = ''
file_name = ''
first_image = ''
is_random = ''
url = ''

#======================== WELCOME MESSAGE ======================================

def welcome_message():
    now = datetime.datetime.now()
    today = now.strftime("%A • %B %e • %H:%M • %Y")
    print('\n  DeviantArt Scraper')
    print('\n  DATE:  ' + today)

#======================== GET USERNAME =========================================

def get_username(d):
    global username
    #html = d.page_source
    #soup = BeautifulSoup(html, 'html.parser')
    username = "" #soup.find(class_='gruserbadge').find('a').get_text()

#======================== GET LINKS FROM TUMBNAILS =============================

def get_thumb_links(q):
    d = get_driver()
    # REPLACE username with your preferred artist
    print('Downloading ' + url)
    d.get(url)
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

    global is_random
    r = -1
    if is_random:
        r = randint(0, 250)

    page = 1
    next = None
    last_height = d.execute_script("return document.body.scrollHeight")

    while ((r == -1 and len(images) < max_image_count) or (r > -1 and len(images) < r + 1)) or max_image_count == 0:
        if next:
            # Navigate to the next page of results.
            url = next[0].get_attribute("href")
            page += 1
            print('Moving to page ' + str(page) + ' at ' + url)
            d.get(url)

        # Get next page.
        try:
            # If a "Next" link exists, get the url for it.
            next = d.find_elements(By.XPATH, "//a[contains(text(), 'Next') and contains(@href,'?cursor=')]")
        except NoSuchElementException:
            print("Skipping next button and using auto-scrolling.")

        if not next:
            # If no "Next" link exists, scroll down to bottom of page.
            print('Auto-scrolling down page.')
            d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME) # Wait to load page
            # Calculate new scroll height and compare with last scroll height
            new_height = d.execute_script("return document.body.scrollHeight")

        # Find all content links on the page.
        im = d.find_elements(By.XPATH, "//div[@data-hook='all_content']")
        links = d.find_elements(By.XPATH, "//a[@data-hook='deviation_link']")

        # Queue unique links.
        for link in links:
            l = link.get_attribute('href')
            if not l in images and (max_image_count == 0 or ((r == -1 and len(images) < max_image_count) or (r > -1 and len(images) < r + 1))):
                print('Queuing ' + l)
                images.append(l)
            else:
                print('Skipping duplicate ' + l)

        # Remove duplicate links.
        unique_img = list(set(images))
        time.sleep(0.5)

        if not next:
            # Break when the end is reached while scrolling down.
            if new_height == last_height:
                break
            last_height = new_height

    if r > 0:
        # Select new index for random image.
        r = randint(0, len(images))
        print("Selecting image " + str(r) + " of " + str(len(images)))
        selected_image = images[r]
        images.clear()
        images.append(selected_image)
        unique_img = list(set(images)) # Remove duplicates

    return unique_img

#======================== GET FULL RESOLUTION IMAGES ===========================

def get_full_image(l):
    s = requests.Session()
    h = {'User-Agent': 'Firefox'}
    soup = BeautifulSoup(s.get(l, headers=h).text, 'html.parser')
    title = ''
    link = ''
    it = None

    try:
        art_stage = soup.find('div', attrs={'data-hook': 'art_stage'})
        img = art_stage.find('img')
        if img:
            link = img['src']
        h1 = soup.find('h1', attrs={'data-hook': 'deviation_title'})
        if h1:
            title = h1.text.replace(' ', '_').lower()
    except TypeError as e:
        print('Error downloading ' + l)
        print(e)

    if link:
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
    d.find_elements(By.CLASS_NAME, 'datefields')
    d.find_elements(By.CLASS_NAME, 'datefield')
    d.find_elements(By.ID, 'month').send_keys('01')
    d.find_elements(By.ID, 'day').send_keys('01')
    d.find_elements(By.ID, 'year').send_keys('1991')
    d.find_elements(By.CLASS_NAME, 'tos-label').click()
    d.find_elements(By.CLASS_NAME, 'submitbutton').click()
    time.sleep(1)
    img_lnk = d.find_elements(By.CLASS_NAME, 'dev-page-download')
    d.get(img_lnk.get_attribute('href'))
    time.sleep(0.5)
    link = d.current_url
    d.close()
    return link

#======================== FILENAME FORMATTING ==================================

def name_format(url,title):
    timestr = time.strftime("%Y-%m-%d-%H-%M-%S")
    name =  title + '_' + timestr
    if title != '':
        name = title + '.jpg'
    return name

#======================== DOWNLOAD USING REQUESTS ==============================

def download_now(req,title):
    global file_name

    url = req.url
    name = file_name or name_format(url,title)
    name = name.replace('/', '_')

    global folder
    pathlib.Path('{}'.format(folder)).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join('{}'.format(folder + name))

    with open(file_path,'wb') as file:
        file.write(req.content)

    # Set image extension by detecting the type of image (jpg, gif, png).
    ext = imghdr.what(file_path) or 'jpg'
    if ext == 'jpeg':
        ext = 'jpg'
    base = os.path.splitext(file_path)[0]
    os.rename(file_path, base + '.' + ext)

    global first_image
    if first_image == '':
        first_image = base + '.' + ext
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
        if p:
            url = p.u
            title = p.t
            name = name_format(url, title)
            with lock:
                save_img(url)
                global img_num
                img_num = img_num + 1
                print('Image ' + str(img_num) + ' ' + name)
        else:
            global no_image_found_count
            no_image_found_count += 1
            print('No image found for ' + link)
        q.task_done()

#======================== MAIN FUNCTION ========================================

def main():
    global folder
    global file_name
    global max_image_count
    global is_random
    global url

    ap = argparse.ArgumentParser()

    # Add the arguments to the parser
    ap.add_argument("-d", "--dir", required=False, help="Directory to store images. Default: ./images", default="images")
    ap.add_argument("-f", "--filename", required=False, help="Explicit base filename to use. Default: downloaded filename", default="")
    ap.add_argument("-u", "--url", required=False, help="DeviantArt gallery url to scrape images from. Default: deviantart.com", default="https://www.deviantart.com")
    ap.add_argument("-c", "--count", required=False, help="Maximum number of images to download. Default: 25", type=int, default=25)
    ap.add_argument("-r", "--random", required=False, help="Download a random image. Default: False", action="store_true")

    # Parse command-line arguments.
    args = vars(ap.parse_args())

    folder = os.path.join(args['dir'].lstrip(), '')
    file_name = args['filename'].lstrip()
    url = args['url'].lstrip()
    max_image_count = args['count']
    is_random = args['random']

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
    if not '/tmp' in folder:
        try:
            folder_size = subprocess.check_output(['du','-shx', folder]).split()[0].decode('utf-8')
            print('\n  Total Images: ' + str(img_num) + ' (' + str(folder_size) + ')')
            print('  Expected: ' + expected_img_num - no_image_found_count)
            end = time.time()
            print('  Elapsed Time: {:.4f}\n'.format(end-start))
        except:
            pass

    if max_image_count == 1:
        global first_image
        print(first_image)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
#===============================================================================