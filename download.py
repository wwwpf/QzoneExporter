import logging
import math
import os
from contextlib import closing
from threading import Lock

import requests

import config
from tools import logging_wrap, purge_file_name

_lock = Lock()


@logging_wrap
def download_media(url, dir, file_name):
    s = "\rdownloading %s -> %05.2f%% "
    chunk_size = 1024
    with requests.get(url, stream=True, timeout=30) as r:
        extension = "jpg"
        if "content-type" in r.headers:
            content_type = r.headers["content-type"]
            extension = content_type[content_type.find("/") + 1:]
        total_len = math.inf
        if "content-length" in r.headers:
            total_len = int(r.headers["content-length"])
        current_len = 0
        file_name = purge_file_name(file_name)
        with _lock:
            if not os.path.exists(dir):
                os.makedirs(dir)
        file_name = os.path.join(dir, "%s.%s" % (file_name, extension))
        with open(file_name, "wb") as f:
            for data in r.iter_content(chunk_size):
                f.write(data)
                current_len += len(data)
                percent = 100 * current_len / total_len
                print(s % (url, percent), end="")
        print("\n%s is downloaded" % url)


@logging_wrap
def export_content_media_url(media, media_type, dir):
    media_id = "%s_id" % media_type
    if media_id not in media:
        logging.warning("%s not found in %s" % (media_id, str(media)))
        return

    media_url = None
    for url_key in config.CONTENT_URL_KEY:
        if url_key in media and len(media[url_key]) > 0:
            media_url = media[url_key]
            break

    if not media_url:
        logging.warning("media url not found in %s" % str(media))
        return

    url_file = os.path.join(dir, config.TO_DOWNLOAD_FILE)
    download_dir = os.path.join(dir, config.DOWNLOAD_PATH)
    with _lock:
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(url_file, "a", encoding="utf-8") as f:
            f.write("%s\t%s\t%s\n" %
                    (media_url, download_dir, media[media_id]))


@logging_wrap
def export_comment_media_url(comment, dir):
    for media_type in config.MEDIA_TYPE:
        if media_type not in comment:
            continue
        medias = comment[media_type]
        for media in medias:
            media_url = None
            for url_key in config.COMMENT_URL_KEY:
                if url_key in media and len(media[url_key]) > 0:
                    media_url = media[url_key]
                    break
            if not media_url:
                s = ("media url not found in %s" % str(media))
                logging.warning(s)
                return

            url_file = os.path.join(dir, config.TO_DOWNLOAD_FILE)
            download_dir = os.path.join(dir, config.DOWNLOAD_PATH)
            with open(url_file, "a", encoding="utf-8") as f:
                f.write("%s\t%s\t%s\n" % (media_url, download_dir, media_url))


class Downloader(object):
    def __init__(self, input_urls_file, output_urls_file, dir):
        self._dir = dir
        self._input_file = os.path.join(dir, input_urls_file)
        self._output_file = os.path.join(dir, output_urls_file)

    @logging_wrap
    def download(self):
        if not os.path.exists(self._input_file):
            logging.warning("%s not exists" % self._input_file)
            return

        print("start downloading")
        with open(self._output_file, "a+", encoding="utf-8") as fupdate:
            with open(self._input_file, "r", encoding="utf-8") as fin:
                fupdate.seek(0)
                done_urls = fupdate.read()

                for line in fin:
                    temp = line.split()
                    url = temp[0]
                    if done_urls.find(url) >= 0:
                        continue

                    download_dir = temp[1]
                    id = temp[2]
                    download_media(url, download_dir, id)
                    fupdate.write("%s\n" % url)
                    fupdate.flush()
        print("downloading done")
