from urllib import request as urlrequest
import brotli
from bs4 import BeautifulSoup
import os
import multiprocessing
import argparse
import re


class RawMangaDownLoader():
    def __init__(self, targetUrl, proxy=None):
        self.targetUrl = targetUrl
        self.proxy = proxy

    def getHeads(self):
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6',
            'Cache-Control': 'max-age=0',
            'pragma': 'no-cache',
            'referer': 'https://rawmangas.net/',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        }

    def run(self):
        req = urlrequest.Request(self.targetUrl)
        proxy = self.proxy
        if proxy:
            req.set_proxy(self.proxy, 'http')
        req.headers = self.getHeads()

        response = urlrequest.urlopen(req)
        content = brotli.decompress(response.read()).decode('UTF-8')

        soup = BeautifulSoup(content, features='html.parser')
        basePath = os.path.join(os.path.curdir, 'out_put')
        if not os.path.exists(basePath):
            os.mkdir(basePath)

        mangaTitle = soup.find(class_='post-title').h1.get_text().strip()
        mangaTitle = re.sub("[\/\\\:\*\?\"\<\>\|\s]+", "_", mangaTitle)
        mangaPath = os.path.join(basePath, mangaTitle)
        downLoadPool = multiprocessing.Pool()

        if not os.path.exists(mangaPath):
            os.mkdir(mangaPath)

        chapters = soup.find_all(class_="wp-manga-chapter")

        chapters = chapters[::-1]
        for chapterIndex in range(len(chapters)):
            chapter = chapters[chapterIndex]
            chapterName = chapter.a.string.strip()
            chapterName = re.sub("[\/\\\:\*\?\"\<\>\|\s+]", "_", chapterName)
            chapterUrl = chapter.a.attrs['href']
            chapterPath = os.path.join(mangaPath, chapterName)

            self.getChapter(chapterPath, chapterUrl, downLoadPool)

        downLoadPool.close()
        downLoadPool.join()

    def getChapter(self, chapterPath, chapterUrl, downLoadPool):
        if not os.path.exists(chapterPath):
            os.mkdir(chapterPath)

        req = urlrequest.Request(chapterUrl)
        proxy = self.proxy
        if proxy:
            req.set_proxy(self.proxy, 'http')
        req.headers = self.getHeads()

        response = urlrequest.urlopen(req)
        content = brotli.decompress(response.read()).decode('UTF-8')

        soup = BeautifulSoup(content, features='html.parser')
        picTags = soup.find_all(class_='page-break')
        for picTag in picTags:
            attrs = picTag.img.attrs
            picUrl = attrs['data-src']

            picName = re.sub("[\/\\\:\*\?\"\<\>\|\s+]", "_", attrs['id'].strip()) + '.' + picUrl.split('.')[-1]
            print(picName)
            picPath = os.path.join(chapterPath, picName)

            # self.downLoadPic(picUrl, picPath)
            downLoadPool.apply_async(self.downLoadPic, (picUrl, picPath), error_callback=lambda err: print(err.__str__))

    def downLoadPic(self, picUrl, picPath):
        req = urlrequest.Request(picUrl)
        proxy = self.proxy
        if proxy:
            req.set_proxy(self.proxy, 'http')
        req.headers = self.getHeads()

        response = urlrequest.urlopen(req)
        content = response.read()

        f = open(picPath, 'wb')
        try:
            f.write(content)
        finally:
            f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', dest='url', required=True,
                        help='start url,must be rawmangas\'s gallery view page,like \'https://rawmangas.net/manga/yuukoku-no-moriarty-raw/\'')
    parser.add_argument('-p', '--proxy', dest='proxy', required=False, help='proxyIp:port,http only')
    args = parser.parse_args()
    url = args.url
    proxy = args.proxy

    # url = 'https://rawmangas.net/manga/youkoso-jitsuryoku-shijou-shugi-no-kyoushitsu-e-raw/'
    # proxy = None

    downLoader = RawMangaDownLoader(url, proxy)
    downLoader.run()
