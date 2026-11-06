#!/usr/bin/env python3
import os

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver_name = 'chromedriver.exe' if os.name == 'nt' else 'chromedriver'
    driver_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), driver_name)

    if os.path.isfile(driver_path):
        try:
            return webdriver.Chrome(options=options, service=Service(executable_path=driver_path))
        except SessionNotCreatedException:
            print('The local ChromeDriver is incompatible; retrying with Selenium Manager.')

    # Selenium Manager locates or downloads the driver compatible with Chrome.
    return webdriver.Chrome(options=options)
