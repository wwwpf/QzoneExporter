import argparse
import json
import logging
import math
import os
from threading import Lock


from account_info import AccountInfo
from blog_parser import BlogComment, BlogInfo, BlogParser
from config import RETRY_TIMES, QzoneFileName, QzonePath
from login import calc_g_tk
from msgborad_parser import MsgBoardParser
from photo_parser import (AlbumInfo, AlbumListInfo, PhotoComment,
                          PhotoCommentDownloader, PhotoDownloader, PhotoParser)
from shuoshuo_parser import ShuoShuoMediaDownloader, ShuoShuoParser
from tools import (get_json_data_from_response, logging_wrap, random_sleep,
                   test_uin_valid)


class QzoneExporter(object):
    '''QQ空间数据导出
    '''

    _logging_inited = False
    _lock = Lock()

    DATA_COUNT_FILE = "like_information.json"
    LIKE_DETAILED_KEY = "like_detailed_data"
    LIKE_COUNT_KEY = "like_count_data"
    ALBUM_LIST_MODE_SORT_KEY = "albumListModeSort"
    ALBUM_LIST_MODE_CLASS_KEY = "albumListModeClass"
    ALBUM_LIST_KEY = "albumList"

    @staticmethod
    def _init_logging():
        FILE_NAME = "log.txt"
        file_handler = logging.FileHandler(FILE_NAME, encoding="utf-8")
        FORMAT = "%(asctime)s %(filename)s[line:%(lineno)d]\t"\
            "%(levelname)s\t%(message)s"
        logging.basicConfig(handlers=[file_handler],
                            level=logging.INFO, format=FORMAT)

    def __init__(self, self_uin, g_tk, cookies_value, args, target_uin=None):

        if not QzoneExporter._logging_inited:
            QzoneExporter._init_logging()
            QzoneExporter._logging_inited = True

        self._account_info = AccountInfo(
            self_uin, g_tk, cookies_value, target_uin)
        self._directory = "%s" % self._account_info.target_uin

        self._main_page_data_get = False

        self._album_num = 0

        self._args = args

        self._func_map = {
            "blog": self._get_blog_data,
            "shuoshuo": self._get_shuoshuo_data,
            "photo": self._get_list_album_data,
            "msgboard": self._get_message_board,
            "download": self._download
        }

        self._can_access = False

    def export(self):
        '''导出数据
        '''

        d = vars(self._args)
        all_options = "all"

        old_flag = d["download"]
        d["download"] = False
        all_flag = False
        for k, v in d.items():
            if v:
                all_flag = True
                break
        # 从本地文件下载数据
        if not all_flag:
            self._func_map["download"]()
            return
        d["download"] = old_flag

        # 从服务器抓取数据
        self._get_main_page_data()
        get_like_data = False
        for option in self._func_map.keys():
            if d[option] or d[all_options]:
                self._func_map[option](get_like_data)

    @property
    def can_access(self):
        return self._can_access

    @logging_wrap
    def _get_main_page_data(self):
        '''获取日志、说说及相册的数量，并测试能否访问目标空间。
        '''

        if self._main_page_data_get:
            return

        main_page_cgi = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/main_page_cgi"
        payload = {
            "uin": self._account_info.target_uin,
            "param": "16",
            "g_tk": self._account_info.g_tk,
        }
        r = self._account_info.get_url(main_page_cgi, params=payload)
        main_json_data = get_json_data_from_response(r.text)

        if not os.path.exists(self._directory):
            os.makedirs(self._directory)

        main_page_file_name = "%s_main_page.json" % self._account_info.target_uin
        filename = os.path.join(self._directory, main_page_file_name)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(main_json_data, f, ensure_ascii=False, indent=4)
            logging.info("save main page data to %s" % filename)

        if main_json_data["code"] != 0:
            print("error:", main_json_data["message"])
            self._can_access = False
            return

        self._can_access = True

        number_data = main_json_data["data"]["module_16"]
        rz = self._account_info.blog_num = number_data["data"]["RZ"]
        ss = self._account_info.shuoshuo_num = number_data["data"]["SS"]
        xc = self._account_info.photo_num = number_data["data"]["XC"]

        print("日志: %d\t说说: %d\t相册: %d\n" % (rz, ss, xc))
        self._main_page_data_get = True

    @logging_wrap
    def _get_blog_data(self, *args, **kwargs):
        '''获取日志数据
        '''
        if not self.can_access:
            return

        # 获取日志数量
        self._get_main_page_data()

        blogs_url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_abs"
        blogs_payload = {
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "format": "jsonp",
            "hostUin": self._account_info.target_uin,
            "uin": self._account_info.self_uin,
            "g_tk": self._account_info.g_tk,
            "pos": "%d" % 0,
            "num": "%d" % 0,
            "blogType": "0",
            "reqInfo": "1"
        }

        single_blog_url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/blog_output_data"
        single_blog_payload = {
            "uin": "%s" % self._account_info.target_uin,
            "blogid": "%s" % "",
            "numperpage": "15",
            "inCharset": "utf-8",
            "outCharset": "utf-8 ",
            "ref": "qzone"
        }

        # 最多100篇日志
        num = 100
        loop_num = math.ceil(self._account_info.blog_num / num)

        total_num = 0
        for i in range(loop_num):
            pos = i * num
            current_num = num if i < loop_num - 1 else self._account_info.blog_num - i * num
            blogs_payload["pos"] = "%d" % pos
            blogs_payload["num"] = "%d" % current_num
            r = self._account_info.get_url(blogs_url, params=blogs_payload)
            json_data = get_json_data_from_response(r.text)
            for blog in json_data["data"]["list"]:
                title = blog["title"]
                print("process blog:", title)

                blog_id = blog["blogId"]
                category = blog["cate"]
                comment_num = blog["commentNum"]
                blog_info = BlogInfo(category, title, blog_id, comment_num)
                statistical_json_data = self._get_blog_comment_data(blog_info)

                single_blog_payload["blogid"] = "%s" % blog_id
                temp = self._account_info.get_url(
                    single_blog_url, params=single_blog_payload)

                read = 0
                try:
                    new_data = statistical_json_data["data"][0]["current"]["newdata"]
                    if new_data and len(new_data) > 0:
                        read = new_data["RZRD"]
                except Exception as e:
                    print("get read num error")
                    print(e)
                    logging.exception(blog_info)
                    logging.exception(e)

                single_blog = BlogParser(
                    self._directory, blog_info, temp.text, read)
                single_blog.export()

            total_num += len(json_data["data"]["list"])
            print("current get %d blog(s)" % total_num)

        if total_num != self._account_info.blog_num:
            logging.warning("qq %s: not get encough blog, get: %d, should get: %d"
                            % (self._account_info.target_uin, total_num,
                               self._account_info.blog_num))

    @logging_wrap
    def _get_blog_comment_data(self, blog_info):
        '''获取日志评论及点赞数据
        '''

        if not self.can_access:
            return

        unikey = "http://user.qzone.qq.com/%s/blog/%s" % (
            self._account_info.target_uin, blog_info.blog_id)
        statistical_json_data = self._get_like_data(unikey)
        comment_num = blog_info.comment_num

        print("process blog comment, [%s]\tid: %s\tcomment_num: %d" %
              (blog_info.title, blog_info.blog_id, comment_num))

        comment_url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_comment_list"

        start = 0
        # 每次最多获取50条评论
        num = 50

        payload = {
            "inCharset": "gb2312",
            "outCharset": "gb2312",
            "format": "jsonp",
            "uin": self._account_info.target_uin,
            "g_tk": self._account_info.g_tk,
            "start": "%d" % start,
            "num": "%d" % num,
            "topicId": "%s_%s" % (self._account_info.target_uin, blog_info.blog_id)
        }

        loop_num = math.ceil(comment_num / num)
        total_num = 0
        for i in range(loop_num):
            start = i * num
            current_num = num if i < loop_num - 1 else comment_num - i * num
            payload["start"] = "%d" % start
            payload["num"] = "%d" % current_num
            print("blog: %s, comment: [%d, %d)" % (
                blog_info.title, start, start + current_num))
            r = self._account_info.get_url(comment_url, params=payload)
            json_data = get_json_data_from_response(r.text)
            if "comments" in json_data["data"]:
                total_num += len(json_data["data"]["comments"])

            blog_comment = BlogComment(
                json_data, start, start + current_num, blog_info, self._directory)
            blog_comment.export()
            random_sleep(0, 1)

        if total_num != comment_num:
            logging.warning("qq %s: not get correct blog comment, "
                            "blog: %s, comment get: %d, comment should get: %d"
                            % (self._account_info.target_uin, blog_info.title,
                               total_num, comment_num))

        return statistical_json_data

    @logging_wrap
    def _get_shuoshuo_data(self, get_like_data=False, *args, **kwargs):
        '''获取说说数据
        '''

        if not self.can_access:
            return

        self._get_main_page_data()

        msglist_url = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"

        num = 40
        loop_num = math.ceil(self._account_info.shuoshuo_num / num)
        payload = {
            "format": "jsonp",
            "need_private_comment": "1",
            "uin": self._account_info.target_uin,
            "pos": "%d" % 0,
            "num": "%d" % num,
            "g_tk": self._account_info.g_tk
        }

        total_num = 0
        for i in range(loop_num):
            pos = i * num
            current_num = num if i < loop_num - \
                1 else self._account_info.shuoshuo_num - i * num
            payload["pos"] = "%d" % (i * num)
            payload["num"] = "%d" % current_num

            r = self._account_info.get_url(msglist_url, params=payload)

            json_data = get_json_data_from_response(r.text)
            if "msglist" in json_data:
                if not json_data["msglist"]:
                    print("msglist is null, break")
                    break
                current_num = len(json_data["msglist"])
                total_num += current_num
            ss_parser = ShuoShuoParser(
                self._account_info, json_data, pos, pos + current_num, self._directory)
            ss_parser.export()

        if total_num != self._account_info.shuoshuo_num:
            logging.warning("qq %s: not get correct shuoshuo, get: %d, should get: %d"
                            % (self._account_info.target_uin, total_num,
                               self._account_info.shuoshuo_num))

        if not get_like_data:
            return
        self._get_shuoshuo_like_data()

    @logging_wrap
    def _get_shuoshuo_like_data(self):
        '''获取说说点赞数据
        '''

        if not self.can_access:
            return

        unikey_pattern = "http://user.qzone.qq.com/%s/mood/%s"
        file = os.path.join(
            self._directory, QzonePath.SHUOSHUO, QzoneFileName.SHUOSHUO_TID)
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                shuoshuo_tid = line.strip("\n")
                unikey = unikey_pattern % (
                    self._account_info.target_uin, shuoshuo_tid)
                self._get_like_data(unikey)
                random_sleep(1, 2)

    @logging_wrap
    def _delete_shuoshuo(self, tid):
        '''删除tid对应说说
        '''

        host_uin = self._account_info.target_uin
        if not self._account_info.is_self():
            return

        delete_url_pattern = "https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_delete_v6"
        form_data = {
            "hostuin": host_uin,
            "tid": tid,
            "qzreferrer": "https://user.qzone.qq.com/%s" % host_uin
        }
        payload = {"g_tk": self._account_info.g_tk}
        return self._account_info.post_url(delete_url_pattern, data=form_data, params=payload)

    @logging_wrap
    def _delete_all_shuoshuo(self):
        '''根据文件中的说说tid删除所有说说。频繁删除会出现验证码
        '''

        if not self._account_info.is_self():
            return

        file = os.path.join(
            self._directory, QzonePath.SHUOSHUO, QzoneFileName.SHUOSHUO_TID)
        count = 0
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                count += 1
                shuoshuo_tid = line.strip("\n")
                self._delete_shuoshuo(shuoshuo_tid)
                print(count, "delete tid:", shuoshuo_tid)
                random_sleep(0, 1)

    @staticmethod
    def _get_album_list_data_len(album_list_data):
        album_list_len = 0
        if QzoneExporter.ALBUM_LIST_MODE_SORT_KEY in album_list_data:
            # 普通视图
            return len(album_list_data[QzoneExporter.ALBUM_LIST_MODE_SORT_KEY] or [])
        elif QzoneExporter.ALBUM_LIST_MODE_CLASS_KEY in album_list_data:
            # 分类视图
            for temp_album in album_list_data[QzoneExporter.ALBUM_LIST_MODE_CLASS_KEY]:
                if QzoneExporter.ALBUM_LIST_KEY in temp_album:
                    album_list_len += len(
                        temp_album[QzoneExporter.ALBUM_LIST_KEY] or [])
        return album_list_len

    @logging_wrap
    def _get_list_album_data(self, get_like_data=False, *args, **kwargs):
        '''获取相册数据
        '''

        if not self.can_access:
            return

        album_list_url = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3"
        pos = 0
        num = 100
        current_num = num

        payload = {
            "g_tk": self._account_info.g_tk,
            "uin": self._account_info.self_uin,
            "hostUin": self._account_info.target_uin,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "source": "qzone",
            "plat": "qzone",
            "pageStart": "%d" % pos,
            "pageNum": "%d" % current_num
        }

        for i in range(RETRY_TIMES):
            r = self._account_info.get_url(album_list_url, params=payload)
            json_data = get_json_data_from_response(r.text)
            result_code = json_data["code"]
            if result_code == 0:
                break
            random_sleep(1, 2)

        if result_code != 0:
            return

        # 返回的相册列表根据相册的展示设置在不同的位置中
        # 普通视图：albumListModeSort，json_data["data"][key]是相册列表
        # 分类视图：albumListModeClass，(json_data["data"][key]的元素)["albumList"]是相册列表
        album_list_mode_key = QzoneExporter.ALBUM_LIST_MODE_SORT_KEY
        if album_list_mode_key not in json_data["data"]:
            album_list_mode_key = QzoneExporter.ALBUM_LIST_MODE_CLASS_KEY
            if album_list_mode_key not in json_data["data"]:
                logging.warning("album list data not found in %s"
                                % json_data["data"])
                return
        if not json_data["data"][album_list_mode_key]:
            logging.warning("%s\nalbum list data is null" %
                            json_data["data"])

        self._album_num = albums_num = json_data["data"]["albumsInUser"]
        print("total album num", self._album_num)

        current_num = QzoneExporter._get_album_list_data_len(json_data["data"])
        total_num = current_num
        loop_num = math.ceil(albums_num / num)
        for i in range(1, loop_num):
            pos = i * num
            current_num = num if i < loop_num - 1 else albums_num - (i * num)
            payload["pageStart"] = "%d" % pos
            payload["pageNum"] = "%d" % current_num
            for i in range(RETRY_TIMES):
                r = self._account_info.get_url(album_list_url, params=payload)
                temp_json_data = get_json_data_from_response(r.text)
                result_code = temp_json_data["code"]
                if result_code == 0:
                    break
                random_sleep(1, 2)
            if result_code != 0:
                continue

            if album_list_mode_key in temp_json_data["data"]:
                if not temp_json_data["data"][album_list_mode_key]:
                    print("album is null, break")
                    break
                total_num += QzoneExporter._get_album_list_data_len(
                    temp_json_data["data"])

            json_data["data"][album_list_mode_key] += temp_json_data["data"][album_list_mode_key]

            print("current get num", total_num)
            random_sleep(0, 1)

        album_list_info = AlbumListInfo(json_data, self._directory)
        album_list_info.export()

        if not album_list_info.json_data["data"][album_list_mode_key]:
            return

        album_list_data = []
        if album_list_mode_key == QzoneExporter.ALBUM_LIST_MODE_SORT_KEY:
            album_list_data = album_list_info.json_data["data"][album_list_mode_key]
        else:
            for temp_album in album_list_info.json_data["data"][album_list_mode_key]:
                if QzoneExporter.ALBUM_LIST_KEY in temp_album:
                    album_list_data += temp_album[QzoneExporter.ALBUM_LIST_KEY]

        for album_data in album_list_data:
            album_info = AlbumInfo(album_data)
            print(str(album_info))

            album_comment_num = self._get_album_comment_data(album_info)
            self._get_album_photo_data(album_info, album_comment_num == 0)

            if get_like_data:
                unikey = "http://user.qzone.qq.com/%s/photo/%s" % (
                    self._account_info.target_uin, album_info.id)
                self._get_like_data(unikey)

            random_sleep(1, 2)

    @logging_wrap
    def _get_album_photo_data(self, album_info, need_get_comment=False):
        '''获取相册中照片数据
        '''

        if not self.can_access:
            return

        print("process album, name: %s\tid: %s" %
              (album_info.name, album_info.id))

        list_photo_url = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_list_photo"
        floatview_photo_list = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_floatview_photo_list_v2"
        start = 0
        num = 500
        current_num = num

        list_photo_payload = {
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "g_tk": self._account_info.g_tk,
            "hostUin": self._account_info.target_uin,
            "uin": self._account_info.self_uin,
            "topicId": album_info.id,
            "pageStart": "%d" % start,
            "pageNum": "%d" % current_num,
        }
        floatview_photo_payload = {
            "g_tk": self._account_info.g_tk,
            "topicId": album_info.id,
            "hostUin": self._account_info.target_uin,
            "uin": self._account_info.self_uin,
            "fupdate": "1",
            "plat": "qzone",
            "source": "qzone",
            "cmtNum": "99",                 # 必选
            "sortOrder": "1",
            "need_private_comment": "1",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "appid": "4",
            "isFirst": "1",
            "picKey": "unknow",
            "postNum": "0"                  # 获取后续照片数量
        }

        ttt = '''{"data": {"comments":[]}}'''
        single_comment_data = json.loads(ttt)
        comment_exported_num = 0
        total_comment_num = 0

        loop_num = math.ceil(album_info.photo_num / num)
        for i in range(loop_num):
            start = i * num
            current_num = num if i < loop_num - 1 else album_info.photo_num - i * num
            list_photo_payload["pageStart"] = "%d" % start
            list_photo_payload["pageNum"] = "%d" % current_num
            r = self._account_info.get_url(
                list_photo_url, params=list_photo_payload)
            json_data = get_json_data_from_response(r.text)
            photo_parser = PhotoParser(
                json_data, start, start + current_num, self._directory, album_info.directory)
            photo_parser.export()

            # 获取原图及视频url
            if "photoList" in json_data["data"] and json_data["data"]["photoList"] \
                    and len(json_data["data"]["photoList"]) > 0:
                floatview_photo_payload["picKey"] = json_data["data"]["photoList"][0]["lloc"]
                floatview_photo_payload["postNum"] = "%d" % (current_num - 1)
                r = self._account_info.get_url(
                    floatview_photo_list, params=floatview_photo_payload)
                floatview_json_data = get_json_data_from_response(r.text)
                photo_parser = PhotoParser(floatview_json_data, start, start + current_num,
                                           self._directory, album_info.directory, True)
                photo_parser.export()

                # 获取评论数据
                if need_get_comment:
                    for photo in json_data["data"]["photoList"]:
                        pic_comment_num = photo["forum"] or 0
                        if pic_comment_num == 0:
                            continue
                        print("find %d comment(s) in %s" %
                              (pic_comment_num, photo["lloc"]))
                        # 评论数可能显示错误
                        floatview_photo_payload["cmtNum"] = "%d" % (
                            pic_comment_num if pic_comment_num > 99 else 99)
                        floatview_photo_payload["picKey"] = photo["lloc"]
                        floatview_photo_payload["postNum"] = "0"

                        r = self._account_info.get_url(floatview_photo_list,
                                                       params=floatview_photo_payload)
                        floatview_json_data = get_json_data_from_response(
                            r.text)
                        if not ("single" in floatview_json_data["data"]
                                and floatview_json_data["data"]["single"]):
                            continue
                        comment_data = floatview_json_data["data"]["single"]["comments"]
                        single_comment_data["data"]["comments"] += comment_data
                        pic_comment_num = len(comment_data)
                        total_comment_num += pic_comment_num
                        if total_comment_num > 100 + comment_exported_num:
                            photo_comment = PhotoComment(single_comment_data,
                                                         comment_exported_num,
                                                         total_comment_num,
                                                         self._directory,
                                                         album_info.directory,
                                                         self._account_info)
                            photo_comment.export()
                            single_comment_data["data"]["comments"] = []
                            comment_exported_num = total_comment_num
                        random_sleep(0, 1)

            random_sleep(1, 2)

        # 导出剩余评论数据
        if need_get_comment:
            if comment_exported_num < total_comment_num:
                photo_comment = PhotoComment(single_comment_data, comment_exported_num,
                                             total_comment_num, self._directory,
                                             album_info.directory, self._account_info)
                photo_comment.export()
            print("get %d comment(s) in %s" %
                  (total_comment_num, album_info.name))

        print(str(album_info), "photo data done")

    @logging_wrap
    def _get_album_comment_data(self, album_info):
        '''获取指定相册的评论数据
        '''

        if not self.can_access:
            return

        comment_url = "https://h5.qzone.qq.com/proxy/domain/app.photo.qzone.qq.com/cgi-bin/app/cgi_pcomment_xml_v2"
        payload = {
            "inCharset": "utf-8",                       # inCharset 必选
            "outCharset": "utf-8",                      # outCharset 必选
            "g_tk": self._account_info.g_tk,
            "hostUin":  self._account_info.target_uin,
            "uin": self._account_info.self_uin,
            "topicId": album_info.id,                   # topicId 必选，相册id
            "order": "1",
            "start": "0",
            "num": "0"                                  # num最大可设定为100
        }
        num = 100
        start = 0
        while True:
            payload["start"] = "%s" % start
            payload["num"] = "%s" % num

            r = self._account_info.get_url(comment_url, params=payload)
            json_data = get_json_data_from_response(r.text)

            if "comments" not in json_data["data"] or len(json_data["data"]["comments"]) == 0:
                break

            current_num = len(json_data["data"]["comments"])

            photo_comment = PhotoComment(json_data, start, start + current_num,
                                         self._directory, album_info.directory,
                                         self._account_info)

            photo_comment.export()

            start += current_num
        if start == 0:
            print("get 0 comment, try to find comments by traversing album")

        print(str(album_info), "comment[%d] done" % start)

        return start

    @logging_wrap
    def _get_like_data(self, unikey):
        '''获取unikey对应的点赞数据
        '''

        if not self.can_access:
            return

        print("process like data:", unikey)

        data_count_file = os.path.join(
            self._directory, QzoneExporter.DATA_COUNT_FILE)
        with QzoneExporter._lock:
            if not os.path.exists(data_count_file):
                with open(data_count_file, "w", encoding="utf-8") as f:
                    f.write("{\n}")
        json_data = None
        like_count = 0
        with open(data_count_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # 获取点赞数据
        like_count_url = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2"
        payload = {
            "fupdate": "1",
            "unikey": unikey,
            "g_tk": self._account_info.g_tk
        }
        r = self._account_info.get_url(like_count_url, params=payload)
        unikey_json_data = get_json_data_from_response(r.text)
        try:
            like_count = unikey_json_data["data"][0]["current"]["likedata"]["cnt"]
        except Exception as e:
            print(e)
            logging.exception("unikey: %s" % unikey)
            logging.exception(unikey_json_data)
            logging.exception(e)
            like_count = 0

        json_data[unikey] = {}
        json_data[unikey][QzoneExporter.LIKE_COUNT_KEY] = unikey_json_data

        if like_count <= 0:
            print(unikey, "has no like data")
            json_data[unikey][QzoneExporter.LIKE_DETAILED_KEY] = "no like detailed data"
        else:
            # 获取点赞详细信息
            like_data_url = "https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app"
            begin_uin = "0"
            query_count = 60
            if_first_page = 1
            current_get_num = 0
            total_num = 0
            payload = {
                "uin": self._account_info.self_uin,
                "unikey": unikey,
                "begin_uin": begin_uin,
                "query_count": "%d" % query_count,
                "if_first_page": "%d" % if_first_page,
                "g_tk": self._account_info.g_tk
            }

            json_data[unikey][QzoneExporter.LIKE_DETAILED_KEY] = []
            while True:
                payload["begin_uin"] = begin_uin
                payload["query_count"] = "%d" % query_count
                payload["if_first_page"] = "%d" % if_first_page
                r = self._account_info.get_url(
                    like_data_url, params=payload)
                temp = r.text
                temp = temp[temp.find("{"): temp.rfind("}") + 1]
                # 中文乱码
                # 需要先用iso8859编码，再解码
                temp_bytes = temp.encode("iso8859")
                try:
                    try:
                        temp = temp_bytes.decode("utf-8")
                    except UnicodeError:
                        temp = temp_bytes.decode("gb2312")
                except Exception as e:
                    logging.exception(e)
                    logging.exception("=====\nerror: %s\n=====" % temp)
                    print("decode error, break")
                    break

                like_json_data = json.loads(temp)
                json_data[unikey][QzoneExporter.LIKE_DETAILED_KEY].append(
                    like_json_data)

                if "data" not in like_json_data:
                    break

                like_uin_info = like_json_data["data"]["like_uin_info"]
                if len(like_uin_info) == 0:
                    break
                begin_uin = like_uin_info[-1]["fuin"]
                if_first_page = 0

                current_get_num = like_json_data["data"]["total_number"]
                total_num += current_get_num
                if current_get_num <= 0 or total_num >= like_count:
                    break

                random_sleep(1, 2)

        with open(data_count_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        return unikey_json_data

    @logging_wrap
    def _get_message_board(self, *args, **kwargs):
        '''获取留言板数据
        '''

        if not self.can_access:
            return

        url_pattern = "https://user.qzone.qq.com/proxy/domain/m.qzone.qq.com/cgi-bin/new/get_msgb"
        num = 20
        pos = 0
        result_code = 0

        payload = {
            "format": "jsonp",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "uin": self._account_info.self_uin,
            "hostUin": self._account_info.target_uin,
            "start": "%d" % pos,
            "num": "%d" % num,
            "g_tk": self._account_info.g_tk,
        }

        # 获取前20条留言及留言总数
        for i in range(RETRY_TIMES):
            r = self._account_info.get_url(url_pattern, params=payload)
            json_data = get_json_data_from_response(r.text)
            result_code = json_data["code"]
            if result_code == 0:
                break
            random_sleep(1, 2)

        if result_code != 0:
            return

        current_num = len(json_data["data"]["commentList"])
        msg_parser = MsgBoardParser(
            json_data, pos, pos + current_num, self._directory)
        msg_parser.export()
        msg_num = json_data["data"]["total"]
        total_num = current_num
        print("current get msgboard num", total_num)

        # 处理剩余留言
        loop_num = math.ceil(msg_num / num)
        for i in range(1, loop_num):
            pos = i * num
            current_num = num if i < loop_num - 1 else msg_num - (i * num)
            payload["start"] = "%d" % pos
            payload["num"] = "%d" % current_num
            for i in range(RETRY_TIMES):
                r = self._account_info.get_url(url_pattern, params=payload)
                json_data = get_json_data_from_response(r.text)
                result_code = json_data["code"]
                if result_code == 0:
                    break
                random_sleep(1, 2)
            if result_code != 0:
                continue

            if "commentList" in json_data["data"]:
                total_num += len(json_data["data"]["commentList"])
            msg_parser = MsgBoardParser(
                json_data, pos, pos + current_num, self._directory)
            msg_parser.export()

            print("current get msgboard num", total_num)
            random_sleep(0, 1)

        if total_num != msg_num:
            logging.warning("qq %s: not get correct msg in msg_board, get: %d\t, should get: %d" %
                            (self._account_info.target_uin, total_num, msg_num))

    @logging_wrap
    def _download(self, *args, **kwargs):
        shuoshuo_media_downloader = ShuoShuoMediaDownloader(self._directory)
        shuoshuo_media_downloader.download()
        photo_downloader = PhotoDownloader(self._directory)
        photo_downloader.download()

        photo_dir = os.path.join(self._directory, QzonePath.PHOTO)
        if not os.path.exists(photo_dir):
            return
        files = os.listdir(photo_dir)
        for album_dir in files:
            if not os.path.isdir(album_dir):
                continue
            comment_downloader = PhotoCommentDownloader(album_dir)
            comment_downloader.download()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--blog", help="导出日志数据", action="store_true")
    parser.add_argument("--msgboard", help="导出留言板数据", action="store_true")
    parser.add_argument("--photo", help="导出相册数据", action="store_true")
    parser.add_argument("--shuoshuo", help="导出说说数据", action="store_true")
    parser.add_argument(
        "--like", help="[deprecated]导出点赞数据，需要设置--photo或--shuoshuo", action="store_true")
    parser.add_argument(
        "--download", help="下载图片或视频至本地，需要先导出说说或相册的json数据", action="store_true")

    parser.add_argument("--all", help="导出所有数据", action="store_true")

    args = parser.parse_args()

    if args.like and not (args.shuoshuo or args.photo):
        print("选项错误")
        return

    target_uin = ""
    self_uin = ""
    cookies_value = ""
    g_tk = ""  # 可选，为空则通过 cookies 中的 p_skey 计算

    p_skey_string = "p_skey="
    while not test_uin_valid(target_uin):
        target_uin = input("请输入需要导出数据的QQ号：")
    while not test_uin_valid(self_uin):
        self_uin = input("请输入用于登录的QQ号：")
    while True:
        if len(cookies_value) == 0:
            cookies_value = input("请输入 cookies：")
        pos = cookies_value.find(p_skey_string)
        p_skey_start = pos + len(p_skey_string)
        p_skey_end = cookies_value.find(";", p_skey_start)
        p_skey_end = p_skey_end if p_skey_end >= 0 else len(cookies_value)
        p_skey = cookies_value[p_skey_start:p_skey_end]
        g_tk = str(calc_g_tk(p_skey))
        if len(g_tk) > 0:
            break

    q = QzoneExporter(self_uin, g_tk, cookies_value, args, target_uin)
    q.export()

    print("done")
    return


if __name__ == "__main__":
    main()
