import threading
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from os import mkdir
from os.path import isfile, isdir, join
import re


class ArticleDownloader:
    def __init__(self):
        self.browser = webdriver.Firefox()

    def __del__(self):
        self.browser.quit()

    def download(self, url):
        if 'about:reader' not in url:
            url = f'about:reader?url={url}'
        self.browser.get(url)
        time.sleep(3)
        content = self.browser.find_element_by_class_name("content")

        ###############################################
        # Content modifications (Not for regular use) #
        ###############################################
        # # Mark list items as lists --> [#],[##], etc until level 10?
        # for i in range(9, -1, -1):
        #     tag = f'[#{"#"*i}]'
        #     for li in self.browser.find_elements_by_xpath(f'//li[count(ancestor::li)={i}]'):
        #         self.browser.execute_script(f'''arguments[0].innerHTML='{tag}'  + arguments[0].innerHTML;''', li)
        #     # Modify clickable links that seem like urls
        # for a in self.browser.find_elements_by_tag_name('a'):
        #     #            url_re = r'https?://((([\w\d]+[.])(com|org|net|co[.]uk|io))|(\d+[.]\d+[.]\d+[.]\d+))/?'
        #     url_re = r'(?:https?):\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        #     if re.search(url_re, a.text) is not None:  # it seems like an url
        #         self.browser.execute_script(f'''arguments[0].innerHTML='LINK';''', a)

        return content.text


class ArticleSaver:
    'Save downloaded articles directly to files'

        def __init__(self, target_directory):
            self.downloader = ArticleDownloader()
            self.target = target_directory
            if not isdir(target_directory):
                mkdir(target_directory)
            self.i = 0

        def save_url(self, url):
            text = self.downloader.download(url)
            tfile = join(self.target, f'{self.i:04d}.txt')
            with open(tfile, 'w') as f:
                f.write(text)


class ArticleMultiSaver:
    'Save downloaded articles directly to files, several at the same time'

    def __init__(self, target_directory, n_workers=4):
        self.downloaders = [ArticleDownloader() for i in range(n_workers)]
        self.target = target_directory
        if not isdir(target_directory):
            mkdir(target_directory)

        self.i = 0
        self.lock = threading.Lock()

    def worker(self, urls, downloader):
        'urls is a generator'
        while True:
            with self.lock:
                try:
                    url = urls.send(None)
                except:
                    return
            i = self.i
            self.i += 1
            text = downloader.download(url)
            tfile = join(self.target, f'{i:04d}.txt')
            with open(tfile, 'w') as f:
                f.write(text)

    def download_urls(self, urls):
        'urls is a generator'
        threads = [threading.Thread(target=self.worker, args=(
            urls, downloader)) for downloader in self.downloaders]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
