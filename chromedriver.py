#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
import sys
import os
import shutil
import pathlib
import urllib.request
import re
import zipfile
import stat
from sys import platform

def get_driver():
    # Attempt to open the Selenium chromedriver. If it fails, download the latest chromedriver.
    driver = None
    retry = True
    major_version = None

    # Determine the version of Chrome installed.
    version = get_chrome_version()
    if version:
        parts = version.split('.')
        major_version = parts[0] if len(parts) > 0 else 0

    while retry:
        retry = False
        is_download = False

        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            executable_path="./chromedriver" + ('.exe' if 'win' in platform else '')
            service = Service(executable_path=executable_path)
            driver = webdriver.Chrome(options=options, service=service)
        except SessionNotCreatedException as e:
            if 'This version of ChromeDriver' in e.msg:
                is_download = True
                print('Warning: You may need to update the Chrome web browser to the latest version. Run Chrome, click Help->About.')
        except WebDriverException as e:
            if "wrong permissions" in e.msg:
                st = os.stat('./chromedriver')
                os.chmod('./chromedriver', st.st_mode | stat.S_IEXEC)
                retry = True
            elif "chromedriver' executable needs to be in PATH" in e.msg:
                is_download = True
            elif "error" in e.msg:
                print(e.msg)
                is_download = True

        retry = is_download and download_driver(major_version)

    return driver

def download_driver(version=None):
    # Find the latest chromedriver, download, unzip, set permissions to executable.
    result = False
    url = 'https://googlechromelabs.github.io/chrome-for-testing'
    base_driver_url = 'https://storage.googleapis.com/chrome-for-testing-public'
    file_name = 'chromedriver-' + get_platform_filename()
    driver_file_name = 'chromedriver' + '.exe' if platform == "win32" else ''
    pattern = 'https://storage.googleapis.com/chrome-for-testing-public/(' + (version or '\d+') + '\.\d+\.\d+\.\d+)'

    # Download latest chromedriver.
    print('Finding latest chromedriver..')
    opener = urllib.request.FancyURLopener({})
    stream = opener.open(url)
    content = stream.read().decode('utf8')

    # Parse the latest version.
    match = re.search(pattern, content)
    if match and match.groups():
        # Url of download html page.
        url = match.group(0)
        # Version of latest driver.
        version = match.group(1)
        driver_url = f"{base_driver_url}/{version}/{get_platform_filename(False)}/{file_name}"

        # Download the file.
        print('Version ' + version)
        print('Downloading ' + driver_url)
        app_path = os.path.dirname(os.path.realpath(__file__))
        chromedriver_path = app_path + '/' + driver_file_name
        file_path = app_path + '/' + file_name
        urllib.request.urlretrieve(driver_url, file_path)

        # Unzip the file.
        print('Unzipping ' + file_path)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(app_path)

        # Copy exe to parent path.
        source_file_path = f"chromedriver-{get_platform_filename(False)}/chromedriver.exe"

        shutil.copyfile(source_file_path, chromedriver_path)
        print('Setting executable permission on ' + chromedriver_path)
        st = os.stat(chromedriver_path)
        os.chmod(chromedriver_path, st.st_mode | stat.S_IEXEC)

        # Cleanup.
        os.remove(file_path)

        result = True

    return result

def get_platform_filename(isExtension=True):
    filename = ''

    is_64bits = sys.maxsize > 2**32

    if platform == "linux" or platform == "linux2":
        # linux
        filename += 'linux64'
    elif platform == "darwin":
        # OS X
        filename += 'mac-x64'
    elif platform == "win32":
        # Windows
        filename += 'win64' if is_64bits else 'win32'

    filename += '.zip' if isExtension else ''

    return filename

def extract_version(output):
    try:
        google_version = ''
        for letter in output[output.rindex('DisplayVersion    REG_SZ') + 24:]:
            if letter != '\n':
                google_version += letter
            else:
                break
        return(google_version.strip())
    except TypeError:
        return

def get_chrome_version():
    version = None
    install_path = None

    try:
        if platform == "linux" or platform == "linux2":
            # linux
            install_path = "/usr/bin/google-chrome"
        elif platform == "darwin":
            # OS X
            install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
        elif platform == "win32":
            # Windows...
            stream = os.popen('reg query "HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome"')
            output = stream.read()
            version = extract_version(output)
    except Exception as ex:
        print(ex)

    version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip() if install_path else version

    return version