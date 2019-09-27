import logging
import math
import os

from config import QzoneFileName, QzoneKey, QzonePath, QzoneType
from download import Downloader
from media_info import export_media_url
from saver import Saver
from tools import get_json_data_from_response, logging_wrap, random_sleep


class ShuoShuoParser(Saver):

    _shuoshuo_count = 0

    def __init__(self, account_info, json_data, begin, end, directory="."):
        Saver.__init__(self, json_data, directory, QzonePath.SHUOSHUO)

        self._account_info = account_info

        self._filename = "shuoshuo_%05d-%05d.json" % (begin, end - 1)

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
    def _parse_all_picture(self, msg):
        floatview_photo_list = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_floatview_photo_list_v2"
        floatview_photo_payload = {
            "g_tk": self._account_info.g_tk,
            "topicId": "%s_%s_1" % (self._account_info.target_uin, msg["tid"]),
            "hostUin": self._account_info.target_uin,
            "uin": self._account_info.self_uin,
            "fupdate": "1",
            "plat": "qzone",
            "source": "qzone",
            "cmtNum": "99",
            "need_private_comment": "1",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "appid": "311",
            "isFirst": "1",
            "picKey": "%s,%s" % (msg["tid"], msg[QzoneType.PICTURE][0][QzoneKey.CONTENT_URL[0]])
        }
        r = self._account_info.get_url(
            floatview_photo_list, params=floatview_photo_payload)
        floatview_json_data = get_json_data_from_response(r.text)
        return floatview_json_data

    @logging_wrap
    def _parse_full_content(self, msg):
        msgdetail = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6"
        msgdetail_payload = {
            "tid": msg["tid"],
            "uin": self._account_info.self_uin,
            "t1_source": "1",
            "not_trunc_con": "1",
            "hostuin": self._account_info.target_uin,
            "code_version": "1",
            "format": "json",
            "qzreferrer": "https://user.qzone.qq.com/%s" % (self._account_info.target_uin),
        }
        msgdetail_params = {
            "g_tk": self._account_info.g_tk
        }

        r = self._account_info.post_url(msgdetail,
                                        params=msgdetail_params,
                                        data=msgdetail_payload)
        r_json = r.json()
        msg["content"] = r_json["content"]
        msg["conlist"] = r_json["conlist"]

    @logging_wrap
    def export(self, need_download_media=False):
        '''默认下载非登录id发表的资源
        '''

        if "msglist" in self.json_data:
            msglist = self.json_data["msglist"]
            tid_file = os.path.join(
                self.directory_path, QzoneFileName.SHUOSHUO_TID)
            with open(tid_file, "a", encoding="utf-8") as f:
                msglist_len = len(msglist)
                for i in range(msglist_len):
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
                                export_media_url(comment, self.directory_path)

                    # 说说图片大于 9 张
                    if QzoneType.PICTURE in msg and msg[QzoneType.PICTURE]\
                            and QzoneKey.PIC_TOTAL in msg and msg[QzoneKey.PIC_TOTAL]\
                            and len(msg[QzoneType.PICTURE]) == 9\
                            and msg[QzoneKey.PIC_TOTAL] > 9:
                        floatview_data = self._parse_all_picture(msg)
                        msglist[i][QzoneKey.OPTION_DATA] = {}
                        msglist[i][QzoneKey.OPTION_DATA][QzoneKey.SHUOSHUO_FLOATVIEW] =\
                            self._parse_all_picture(msg)
                        msg = msglist[i]

                    # 需要获取全文
                    if msg.get("has_more_con"):
                        self._parse_full_content(msg)

                    if self._account_info.target_uin != self._account_info.self_uin \
                            or need_download_media:
                        export_media_url(msg, self.directory_path)

                    ShuoShuoParser._shuoshuo_count += 1

                    if need_sleep:
                        random_sleep(0, 1)

        self.save(self._filename)


class ShuoShuoMediaDownloader(Downloader):
    def __init__(self, directory):
        Downloader.__init__(self, QzoneFileName.TO_DOWNLOAD, QzoneFileName.DOWNLOADED,
                            os.path.join(directory, QzonePath.SHUOSHUO))
