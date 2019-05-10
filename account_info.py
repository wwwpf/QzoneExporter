import logging

import requests

from config import RETRY_TIMES, HEADERS
from tools import logging_wrap


class AccountInfo(object):

    def __init__(self, self_uin, g_tk, cookies_value, target_uin=None):
        self._self_uin = self_uin
        self._g_tk = g_tk

        self._target_uin = target_uin or self_uin
        self._cookies_pair = {"cookie": cookies_value}

        self._blog_num = 0
        self._shuoshuo_num = 0
        self._photo_num = 0

    @property
    def self_uin(self):
        return self._self_uin

    @property
    def g_tk(self):
        return self._g_tk

    @property
    def target_uin(self):
        return self._target_uin

    @property
    def blog_num(self):
        return self._blog_num

    @blog_num.setter
    def blog_num(self, num):
        if num >= 0:
            self._blog_num = num

    @property
    def shuoshuo_num(self):
        return self._shuoshuo_num

    @shuoshuo_num.setter
    def shuoshuo_num(self, num):
        if num >= 0:
            self._shuoshuo_num = num

    @property
    def photo_num(self):
        return self._photo_num

    @photo_num.setter
    def photo_num(self, num):
        if num >= 0:
            self._photo_num = num

    def is_self(self):
        return self._self_uin == self._target_uin

    @logging_wrap
    def get_url(self, url, **kwargs):
        r = None
        for _ in range(RETRY_TIMES):
            r = requests.get(url, headers=HEADERS,
                             cookies=self._cookies_pair, **kwargs)
            if r.ok:
                return r
        logging.exception("get request failed")
        return r

    @logging_wrap
    def post_url(self, url, **kwargs):
        return requests.post(url, headers=HEADERS,
                             cookies=self._cookies_pair, **kwargs)
