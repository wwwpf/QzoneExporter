import json
import logging
import math
import os

import requests

import config
from download import (Downloader, export_comment_media_url,
                      export_content_media_url)
from saver import Saver
from tools import get_json_data_from_response, logging_wrap, random_sleep


class ShuoShuoParser(Saver):

    _shuoshuo_count = 0

    def __init__(self, account_info, json_data, begin, end, dir="."):
        Saver.__init__(self, json_data, dir, config.SHUOSHUO_PATH)

        self._account_info = account_info

        self._file_name = "shuoshuo_%05d-%05d.json" % (begin, end - 1)

    @logging_wrap
    def _parse_single_shuoshuo(self, tid, comment_num):
        single_shuoshuo_url = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6"
        pos = 0
        num = 20

        payload = {
            "format": "jsonp",
            "need_private_comment": "1",
            "uin": self._account_info.target_uin,
            "tid": tid,
            "g_tk": self._account_info.g_tk,
            "pos": "%d" % pos,
            "num": "%d" % num,
        }

        loop_num = math.ceil(comment_num / num)
        total_num = 0
        result = None
        for i in range(0, loop_num):
            pos = i * num
            current_num = num if i < loop_num - 1 else comment_num - (i * num)
            payload["pos"] = "%d" % pos
            payload["num"] = "%d" % current_num
            r = self._account_info.get_url(single_shuoshuo_url, params=payload)
            json_data = get_json_data_from_response(r.text)
            total_num += len(json_data["commentlist"])
            if i == 0:
                result = json_data
            else:
                result["commentlist"] += json_data["commentlist"]
        if total_num != comment_num:
            logging.warning("shuoshuo %s: no get correct comments, "
                            "get: %d, should get: %d" % (tid, total_num, comment_num))
        return result

    @logging_wrap
    def export(self, need_download_media=False):
        '''默认下载非登录id发表的资源
        '''

        if "msglist" in self.json_data:
            msglist = self.json_data["msglist"]
            tid_file = os.path.join(
                self.directory_path, config.SHUOSHUO_TID_FILE)
            with open(tid_file, "a", encoding="utf-8") as f:
                for i in range(0, len(msglist)):
                    msg = msglist[i]
                    print("%05d\t" % ShuoShuoParser._shuoshuo_count,
                          "process shuoshuo, tid:", msg["tid"])
                    f.write("%s\n" % msg["tid"])
                    need_sleep = False

                    comment_num = msg["cmtnum"]
                    if comment_num > 0 and "commentlist" in msg and msg["commentlist"]:
                        comment_list = msg["commentlist"]
                        if len(comment_list) != comment_num:
                            need_sleep = True
                            msg = msglist[i] = self._parse_single_shuoshuo(
                                msg["tid"], comment_num)
                            comment_list = msg["commentlist"]

                        for comment in comment_list:
                            if comment["uin"] != self._account_info.self_uin \
                                    or need_download_media:
                                export_comment_media_url(
                                    comment, self.directory_path)

                    if self._account_info.target_uin != self._account_info.self_uin \
                            or need_download_media:
                        for media_type in config.MEDIA_TYPE:
                            if media_type in msg:
                                medias = msg[media_type]
                                for media in medias:
                                    export_content_media_url(
                                        media, media_type, self.directory_path)

                    ShuoShuoParser._shuoshuo_count += 1

                    if need_sleep:
                        random_sleep(0, 1)

        self.save(self._file_name)


class ShuoShuoMediaDownloader(Downloader):
    def __init__(self, dir):
        Downloader.__init__(self, config.TO_DOWNLOAD_FILE, config.DOWNLOADED_FILE,
                            os.path.join(dir, config.SHUOSHUO_PATH))
