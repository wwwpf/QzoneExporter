import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread

import requests

from tools import get_max_worker, logging_wrap, purge_file_name

thread_pool_executor = ThreadPoolExecutor(get_max_worker())
directory_lock = Lock()
dict_lock = Lock()
_locks = {}


def update_downloaded_file(url, *args, **kwargs):
    if len(url) == 0:
        return
    downloaded_file = kwargs.get("downloaded_file", None)
    if not downloaded_file:
        return
    lock = None
    with dict_lock:
        lock = _locks.setdefault(downloaded_file, Lock())
    with lock:
        with open(downloaded_file, "a", encoding="utf-8") as fout:
            fout.write("%s\n" % url)


def update_downloaded_file_with_check(url, *args, **kwargs):
    if len(url) == 0:
        return
    downloaded_file = kwargs.get("downloaded_file", None)
    if not downloaded_file:
        return
    lock = None
    with dict_lock:
        lock = _locks.setdefault(downloaded_file, Lock())
    with lock:
        with open(downloaded_file, "a+", encoding="utf-8") as fupdate:
            fupdate.seek(0)
            done_urls = fupdate.read()
            if done_urls.find(url) < 0:
                fupdate.write("%s\n" % url)
                fupdate.flush()


@logging_wrap
def download_media(url, directory, filename, has_extension=False, *args, **kwargs):
    result = False
    s = "\rdownloading " + url + " -> %05.2f%% "
    chunk_size = 1024 << 4
    with directory_lock:
        if not os.path.exists(directory):
            os.makedirs(directory)
    lock = None
    with dict_lock:
        lock = _locks.setdefault(url, Lock())
    with lock:
        with requests.get(url, stream=True) as r:
            total_len = math.inf
            if "content-length" in r.headers:
                total_len = int(r.headers["content-length"])
            current_len = 0
            filename = purge_file_name(filename)
            if not has_extension:
                extension = "jpg"
                if "content-type" in r.headers:
                    content_type = r.headers["content-type"]
                    extension = content_type[content_type.find("/") + 1:]
                filename = "%s.%s" % (filename, extension)
            filename = os.path.join(directory, filename)
            if not os.path.exists(filename):
                with open(filename, "wb") as f:
                    for data in r.iter_content(chunk_size):
                        f.write(data)
                        current_len += len(data)
                        percent = 100 * current_len / total_len
                        print(s % (percent), end="")
                result = True
                print("\n%s is downloaded" % url)
    return result


class DownloadThread(Thread):
    def __init__(self, url, directory, filename, record_downloaded, *args, **kwargs):
        super().__init__()
        self._url = url
        self._directory = directory
        self._filename = filename
        self._after_download_function = record_downloaded
        self._args = args
        self._kwargs = kwargs

    def run(self):
        future = thread_pool_executor.submit(
            download_media, self._url, self._directory, self._filename, *self._args, **self._kwargs)
        if future.result():
            self._after_download_function(
                url=self._url, *self._args, **self._kwargs)


class Downloader(object):
    def __init__(self, input_urls_file, output_urls_file, directory):
        self._dir = directory
        self._input_file = os.path.join(directory, input_urls_file)
        self._output_file = os.path.join(directory, output_urls_file)
        self._thread_pool_executor = ThreadPoolExecutor(get_max_worker())

    @logging_wrap
    def download(self):
        if not os.path.exists(self._input_file):
            logging.warning("%s not exists" % self._input_file)
            return

        print("start downloading")
        downloaded_urls = ""
        if os.path.exists(self._output_file):
            with open(self._output_file, "r", encoding="utf-8") as fin:
                downloaded_urls = fin.read()
        threads = []
        with open(self._input_file, "r", encoding="utf-8") as fin:
            for line in fin:
                temp = line.split()
                url = temp[0]
                if downloaded_urls.find(url) >= 0:
                    continue

                download_dir = temp[1]
                filename = temp[2]
                download_thread = DownloadThread(url, download_dir, filename,
                                                 update_downloaded_file_with_check,
                                                 has_extension=False,
                                                 downloaded_file=self._output_file)
                download_thread.start()
                threads.append(download_thread)
        for t in threads:
            t.join()
        print("downloading done")
