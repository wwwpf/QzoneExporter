import json
import os
import re

from bs4 import BeautifulSoup
from flask import redirect, render_template, url_for

from blog_parser import BlogInfo
from config import QzoneFileName, QzonePath, QzoneString
from exporter import QzoneExporter
from tools import (get_files, get_sum_page, recover_file_name,
                   test_album_valid, test_blog_comment_valid, test_blog_valid,
                   test_floatview_photo_valid, test_msgboard_valid,
                   test_photo_comment_valid, test_photo_valid,
                   test_shuoshuo_valid)

NUMBER_PATTERN = re.compile(r"阅读\((\d+?)\).*?评论\((\d+?)\)")
PRIV_MAP = {
    1: {
        "title": "公开",
        "class": "icon-limit-m"
    },
    2: {
        "title": "输入密码可见",
        "class": "icon-pwd-m"
    },
    3: {
        "title": "仅自己可见",
        "class": "icon-private-m"
    },
    4: {
        "title": "QQ好友可见",
        "class": "icon-friend-m"
    },
    5: {
        "title": "回答问题可见",
        "class": "icon-question-m"
    },
    6: {
        "title": "部分好友可见",
        "class": "icon-designated-m"
    },
    8: {
        "title": "部分好友不可见",
        "class": "icon-part-forbidden-m"
    }
}

# 保存相册文件夹与相册id的映射关系
_album_save = {}


class QzoneGenerator(object):

    PATH_TEXTS = {
        QzonePath.SHUOSHUO: QzoneString.SHUOSHUO,
        QzonePath.BLOG: QzoneString.BLOG,
        QzonePath.PHOTO: QzoneString.PHOTO,
        QzonePath.MSG_BOARD: QzoneString.MSGBOARD
    }

    def __init__(self, dir_path, download_if_not_exist=False):

        self._main_dir = dir_path

        self._data_dir = {
            QzonePath.SHUOSHUO: os.path.join(dir_path, QzonePath.SHUOSHUO),
            QzonePath.BLOG: os.path.join(dir_path, QzonePath.BLOG),
            QzonePath.PHOTO: os.path.join(dir_path, QzonePath.PHOTO),
            QzonePath.MSG_BOARD: os.path.join(dir_path, QzonePath.MSG_BOARD)
        }

        self._main_data = {
            QzonePath.SHUOSHUO: 0,
            QzonePath.BLOG: 0,
            QzonePath.PHOTO: 0,
            QzonePath.MSG_BOARD: 0
        }

        self._files = {
            # 说说文件列表
            QzonePath.SHUOSHUO: None,
            # 照片文件列表，以相册 id 为 key
            QzonePath.PHOTO: None,
            QzonePath.MSG_BOARD: None,
            QzonePath.BLOG: None
        }

        self._comment_files = {
            QzonePath.PHOTO: None,  # 以相册 id 为 key
            QzonePath.BLOG: None
        }

        self._total_page = {
            QzonePath.SHUOSHUO: 0,
            QzonePath.MSG_BOARD: 0,
            QzonePath.PHOTO: {},
            QzonePath.BLOG: {}
        }

        self._sum_page = {
            QzonePath.MSG_BOARD: {},
            QzonePath.BLOG: {}
        }

        self._blog_info_list = None
        self._current_blog = None
        self._current_blog_content_div = None

        self._current_album_id = None
        self._current_album_comment_page = None
        self._current_album_comments = []

        self._album_info_dict = None
        self._ablum_name2id = {}

        qzone_name = ""
        self._template_args = {
            "qzone_name": qzone_name if len(qzone_name) else dir_path + "的QQ空间",
            "uin": dir_path,
            "path_texts": self.PATH_TEXTS,
            "main_data": self._main_data,
            "download_if_not_exist": download_if_not_exist
        }

        self._init_statistical_data()

    def generate_home(self):
        return render_template(QzoneFileName.INDEX_HTML, **self._template_args)

    def generate_single_blog(self, encoded_category, blog_id, page=1):
        if not self._blog_info_list:
            self._init_blog_data()

        update = False
        recovered_cate = recover_file_name(encoded_category)
        if self._current_blog is None \
                or self._current_blog.blog_id != blog_id \
                or self._current_blog.category != recovered_cate:

            update = True
            full_category_dir = os.path.join(
                self._data_dir[QzonePath.BLOG], encoded_category)
            if not os.path.exists(full_category_dir):
                return redirect(url_for("uin_home", uin=self._main_dir))
            files = os.listdir(full_category_dir)
            blog_file = None
            str_id = "%s" % blog_id
            for f in files:
                if str_id in f:
                    blog_file = f
                    break
            else:
                return redirect(url_for("uin_home", uin=self._main_dir))

            self._current_blog = self._files[QzonePath.BLOG][recovered_cate][blog_id]

        blog_file = self._current_blog.get_file_name()
        total_page = self._total_page[QzonePath.BLOG].setdefault(blog_file, 0)
        if total_page == 0 and page != 0:
            return redirect(url_for("single_blog", uin=self._main_dir,
                                    encoded_category=encoded_category,
                                    blog_id=blog_id, page=0))
        elif total_page > 0 and page < 1 or page > total_page:
            page = min(total_page, max(1, page))
            return redirect(url_for("single_blog", uin=self._main_dir,
                                    encoded_category=encoded_category,
                                    blog_id=blog_id, page=page))
        comment_list = []
        if total_page > 0:
            comment_file = os.path.join(self._data_dir[QzonePath.BLOG], encoded_category,
                                        self._comment_files[QzonePath.BLOG][blog_file][page - 1])
            with open(comment_file, "r", encoding="utf-8") as fin:
                json_data = json.load(fin)

            comment_list = json_data["data"]["comments"]

        if update:
            full_filename = os.path.join(full_category_dir, blog_file)
            with open(full_filename, "r", encoding="utf-8") as fin:
                bs_obj = BeautifulSoup(fin.read(), "html.parser")
                bs_obj.encode = "utf-8"
                self._current_blog_content_div = \
                    bs_obj.find("div", {"id": "blogDetailDiv"})
                if not self._current_blog_content_div:
                    return redirect(url_for("uin_home", uin=self._main_dir))
        return render_template(QzoneFileName.SINGLE_BLOG_HTML,
                               blog_info=self._current_blog,
                               blog_content_div=self._current_blog_content_div,
                               current_page=page,
                               sum_page=self._sum_page[QzonePath.BLOG][blog_file],
                               total_page=self._total_page[QzonePath.BLOG][blog_file],
                               comments=comment_list,
                               **self._template_args)

    def generate_blog(self, encoded_category=None, blog_id=None, page=1):
        if not self._blog_info_list:
            if not os.path.exists(self._data_dir[QzonePath.BLOG]):
                return redirect(url_for("uin_home", uin=self._main_dir))
            self._init_blog_data()

        if self._main_data[QzonePath.BLOG] <= 0:
            return redirect(url_for("uin_home", uin=self._main_dir))

        if not encoded_category:
            # 全部日志
            return render_template(QzoneFileName.BLOG_PREVIEW_HTML,
                                   blog_list=self._blog_info_list,
                                   categories=self._files[QzonePath.BLOG],
                                   **self._template_args)
        elif not blog_id:
            # 分类日志
            c = recover_file_name(encoded_category)
            return render_template(QzoneFileName.BLOG_PREVIEW_HTML,
                                   blog_list=sort_blog_list_by_time(self._files[QzonePath.BLOG][c].values(
                                   )),
                                   categories=self._files[QzonePath.BLOG],
                                   **self._template_args)
        return self.generate_single_blog(encoded_category, blog_id, page)

    def generate_msg_board(self, page=1):
        if self._total_page[QzonePath.MSG_BOARD] <= 0:
            return redirect(url_for("uin_home", uin=self._main_dir))

        if page < 1 or page > self._total_page[QzonePath.MSG_BOARD]:
            page = min(self._total_page[QzonePath.MSG_BOARD], max(1, page))
            return redirect(url_for("msg_board", uin=self._main_dir, page=page))

        file = os.path.join(self._data_dir[QzonePath.MSG_BOARD],
                            self._files[QzonePath.MSG_BOARD][page - 1])
        with open(file, "r", encoding="utf-8") as fin:
            json_data = json.load(fin)
        commentlist = json_data["data"]["commentList"]
        return render_template(QzoneFileName.MSG_BOARD_HTML,
                               commentlist=commentlist,
                               current_page=page,
                               sum_page=self._sum_page[QzonePath.MSG_BOARD],
                               total_page=self._total_page[QzonePath.MSG_BOARD],
                               author_info=json_data["data"]["authorInfo"],
                               total_msg=self._main_data[QzonePath.MSG_BOARD],
                               **self._template_args)

    def generate_shuoshuo(self, page=1):
        if not self._files[QzonePath.SHUOSHUO]:
            self._files[QzonePath.SHUOSHUO] = []

            self._files[QzonePath.SHUOSHUO] = \
                get_files(
                    self._data_dir[QzonePath.SHUOSHUO], test_shuoshuo_valid)

            self._total_page[QzonePath.SHUOSHUO] = \
                len(self._files[QzonePath.SHUOSHUO])

        if self._total_page[QzonePath.SHUOSHUO] <= 0:
            return redirect(url_for("uin_home", uin=self._main_dir))

        if page < 1 or page > self._total_page[QzonePath.SHUOSHUO]:
            page = min(self._total_page[QzonePath.SHUOSHUO], max(1, page))
            return redirect(url_for("shuoshuo", uin=self._main_dir, page=page))

        file = os.path.join(self._data_dir[QzonePath.SHUOSHUO],
                            self._files[QzonePath.SHUOSHUO][page - 1])
        with open(file, "r", encoding="utf-8") as fin:
            json_data = json.load(fin)
        msglist = json_data["msglist"]
        return render_template(QzoneFileName.SHUOSHUO_HTML, msglist=msglist,
                               current_page=page,
                               total_page=self._total_page[QzonePath.SHUOSHUO],
                               **self._template_args)

    def get_album_comments(self, encoded_album, page=0):
        '''获取指定相册的评论内容与评论文件个数
        Return:
            page为0返回该相册所有评论，大于0返回第page个评论文件的内容
        '''

        album_id, album_dir = self.get_album_id_dir(encoded_album)
        if self._current_album_id == album_id \
                and self._current_album_comment_page == page:
            return self._current_album_comments
        page = max(page, 0)
        comments = []
        comment_files = self._comment_files[QzonePath.PHOTO].get(album_id, [])
        l = len(comment_files)
        if page > 0 and l > 0:
            page = min(page, l)
            comment_files = [comment_files[page-1]]

        for f in comment_files:
            full_file = os.path.join(
                self._data_dir[QzonePath.PHOTO], album_dir, f)
            json_data = None
            with open(full_file, "r", encoding="utf-8") as fin:
                json_data = json.load(fin)
            if "data" in json_data and "comments" in json_data["data"] \
                    and json_data["data"]["comments"]:
                comments += json_data["data"]["comments"]
        if page == 0:
            floatview_photo_files = self._files[QzonePath.PHOTO][album_id]["floatview"]
            for f in floatview_photo_files:
                full_file = os.path.join(
                    self._data_dir[QzonePath.PHOTO], album_dir, f)
                with open(full_file, "r", encoding="utf-8") as fin:
                    json_data = json.load(fin)
                if "single" in json_data["data"] and json_data["data"]["single"]:
                    temp = json_data["data"]["single"]
                    if "comments" in temp and temp["comments"]:
                        comments += temp["comments"]

        self._current_album_comment_page = page
        self._current_album_id = album_id
        self._current_album_comments = comments
        return self._current_album_comments, l

    def generate_dialog_layer(self, encoded_album, _, comment_index=0):
        if not self._album_info_dict:
            self._init_album_info()
        comment_page = comment_index + 1
        photo_comments, total_page = self.get_album_comments(
            encoded_album, comment_page)

        album_id, _ = self.get_album_id_dir(encoded_album)
        album_info = self._album_info_dict[album_id]

        return render_template(QzoneFileName.DIALOG_LAYER_HTML,
                               album_info=album_info,
                               photo_comments=photo_comments,
                               current_page=comment_page,
                               total_page=total_page,
                               **self._template_args)

    def generate_photo_layer(self, encoded_album, page, photo_index=0):
        if not self._album_info_dict:
            self._init_album_info()
        if len(self._album_info_dict) <= 0:
            return redirect(url_for("uin_home", uin=self._main_dir))

        album_id, album_dir = self.get_album_id_dir(encoded_album)
        floatview_photo_file = self._files[QzonePath.PHOTO][album_id]["floatview"][page-1]
        full_file = os.path.join(self._data_dir[QzonePath.PHOTO],
                                 album_dir, floatview_photo_file)
        with open(full_file, "r", encoding="utf-8") as fin:
            json_data = json.load(fin)
        album_info = self._album_info_dict[album_id]
        floatview_photos = json_data["data"]["photos"]
        photo_index = max(min(photo_index, len(floatview_photos)), 0)
        photo_comments, _ = self.get_album_comments(encoded_album, 0)
        return render_template(QzoneFileName.PHOTO_LAYER_HTML, album_info=album_info,
                               photo_index=photo_index,
                               floatview_photos=floatview_photos,
                               photo_comments=photo_comments,
                               **self._template_args)

    def generate_photo(self, encoded_album=None, page=1):
        if not self._album_info_dict:
            self._init_album_info()
        if len(self._album_info_dict) <= 0:
            return redirect(url_for("uin_home", uin=self._main_dir))

        if not encoded_album:
            return render_template(QzoneFileName.ALBUM_HTML,
                                   album_info_list=self._album_info_dict.values(),
                                   priv_map=PRIV_MAP,
                                   **self._template_args)

        album_id, album_dir = self.get_album_id_dir(encoded_album)
        total_page = len(self._files[QzonePath.PHOTO].get(
            album_id, {}).get("floatview", []))
        if total_page <= 0:
            return redirect(url_for("album", uin=self._main_dir))

        if page < 1 or page > total_page:
            page = min(total_page, max(1, page))
            return redirect(url_for("photo", uin=self._main_dir,
                                    encoded_album=encoded_album,
                                    page=page))

        floatview_photo_file = self._files[QzonePath.PHOTO][album_id]["floatview"][page-1]
        full_file = os.path.join(self._data_dir[QzonePath.PHOTO],
                                 album_dir, floatview_photo_file)
        with open(full_file, "r", encoding="utf-8") as fin:
            json_data = json.load(fin)
        floatview_photos = json_data["data"]["photos"]

        photo_comments_page = len(
            self._comment_files[QzonePath.PHOTO].get(album_id, []))
        album_info = self._album_info_dict[album_id]
        return render_template(QzoneFileName.PHOTO_HTML, album_info=album_info,
                               priv_map=PRIV_MAP, current_page=page,
                               total_page=total_page,
                               floatview_photos=floatview_photos,
                               photo_comments_page=photo_comments_page,
                               **self._template_args)

    def _init_statistical_data(self):
        '''初始化说说、相册、留言板、日志数量
        '''

        if not self._files[QzonePath.MSG_BOARD]:
            self._files[QzonePath.MSG_BOARD] = get_files(
                self._data_dir[QzonePath.MSG_BOARD], test_msgboard_valid)

            self._sum_page[QzonePath.MSG_BOARD] = get_sum_page(
                self._files[QzonePath.MSG_BOARD])
            self._main_data[QzonePath.MSG_BOARD] = self._sum_page[QzonePath.MSG_BOARD][len(
                self._files[QzonePath.MSG_BOARD])]
            self._total_page[QzonePath.MSG_BOARD] = len(
                self._files[QzonePath.MSG_BOARD])

        main_page_file_name = "%s_main_page.json" % self._main_dir
        filename = os.path.join(self._main_dir, main_page_file_name)
        if not os.path.exists(filename):
            return
        json_data = None
        with open(filename, "r", encoding="utf-8") as fin:
            json_data = json.load(fin)

        if json_data is None:
            return

        data = json_data["data"]["module_16"]["data"]
        self._main_data[QzonePath.SHUOSHUO] = data["SS"]
        self._main_data[QzonePath.BLOG] = data["RZ"]
        self._main_data[QzonePath.PHOTO] = data["XC"]

    def _init_album_info(self):
        '''初始化相册数据
        '''

        self._album_info_dict = {}
        self._files[QzonePath.PHOTO] = {}
        self._comment_files[QzonePath.PHOTO] = {}

        album_info_file = os.path.join(
            self._data_dir[QzonePath.PHOTO], QzoneFileName.PHOTO_ALBUM_INFO)

        if not os.path.exists(album_info_file):
            return

        json_data = None
        with open(album_info_file, "r", encoding="utf-8") as fin:
            json_data = json.load(fin)

        album_list_mode_key = QzoneExporter.ALBUM_LIST_MODE_SORT_KEY
        if album_list_mode_key not in json_data["data"]:
            album_list_mode_key = QzoneExporter.ALBUM_LIST_MODE_CLASS_KEY
            if album_list_mode_key not in json_data["data"]:
                return
        if not json_data["data"][album_list_mode_key]:
            return
        temp = json_data["data"][album_list_mode_key]
        for album in temp:
            self._album_info_dict[album["id"]] = album

        if not os.path.exists(self._data_dir[QzonePath.PHOTO]):
            return
        files = os.listdir(self._data_dir[QzonePath.PHOTO])
        for f in files:
            album_dir = os.path.join(self._data_dir[QzonePath.PHOTO], f)
            if not os.path.isdir(album_dir):
                continue
            s = test_album_valid(f)
            if not s:
                continue
            encoded_album_name = s[1]
            album_id = s[2]

            self._ablum_name2id[encoded_album_name] = album_id

            album_files = os.listdir(album_dir)
            for t in album_files:
                if test_photo_valid(t):
                    self._files[QzonePath.PHOTO].setdefault(
                        album_id, {}).setdefault("photo", []).append(t)
                elif test_floatview_photo_valid(t):
                    self._files[QzonePath.PHOTO].setdefault(
                        album_id, {}).setdefault("floatview", []).append(t)
                elif test_photo_comment_valid(t):
                    self._comment_files[QzonePath.PHOTO].setdefault(
                        album_id, []).append(t)

    def _init_blog_data(self):
        '''初始化日志数据
        '''

        self._blog_info_list = []
        self._comment_files[QzonePath.BLOG] = {}
        self._files[QzonePath.BLOG] = {}

        categories = os.listdir(self._data_dir[QzonePath.BLOG])
        for encoded_cate in categories:
            encoded_cate_dir = os.path.join(
                self._data_dir[QzonePath.BLOG], encoded_cate)
            if not os.path.isdir(encoded_cate_dir):
                continue
            files = os.listdir(encoded_cate_dir)
            for encoded_file in files:
                s = test_blog_valid(encoded_file)
                if not s:
                    continue
                blog_info = get_blog_info(
                    self._data_dir[QzonePath.BLOG], encoded_cate, encoded_file, s)
                if not blog_info:
                    continue
                self._blog_info_list.append(blog_info)
                self._files[QzonePath.BLOG].setdefault(
                    blog_info.category, {})[blog_info.blog_id] = blog_info
                self._comment_files[QzonePath.BLOG][encoded_file] = []

            for encoded_file in files:
                s = test_blog_comment_valid(encoded_file)
                if not s:
                    continue
                html_f = "%s.html" % s[1]
                self._comment_files[QzonePath.BLOG].setdefault(
                    html_f, []).append(encoded_file)


            for k, v in self._comment_files[QzonePath.BLOG].items():
                self._comment_files[QzonePath.BLOG][k] = sorted(v)
                self._sum_page[QzonePath.BLOG][k] = \
                    get_sum_page(self._comment_files[QzonePath.BLOG][k])
                self._total_page[QzonePath.BLOG][k] = len(v)
        self._blog_info_list = sort_blog_list_by_time(self._blog_info_list)
        self._main_data[QzonePath.BLOG] = len(self._blog_info_list)

    def get_album_id_dir(self, encoded_album):
        t = _album_save.setdefault(self._main_dir, {})
        if encoded_album in t:
            return t[encoded_album]
        album_id = self._ablum_name2id[encoded_album]
        album_dir = "%s_%s" % (encoded_album, album_id)
        t[encoded_album] = (album_id, album_dir)
        return t[encoded_album]


def get_blog_info(directory, encoded_category, encoded_filename, matched_result):
    ''' 获取日志基本信息：标题、分类、id、评论数、阅读数
    '''

    read_num = 0
    comment_num = 0
    blog_title = matched_result[1]
    blog_id = int(matched_result[2])

    blog_info = None
    full_filename = os.path.join(directory, encoded_category, encoded_filename)
    with open(full_filename, "r", encoding="utf-8") as fin:
        m = NUMBER_PATTERN.search(fin.read())
        if m:
            read_num = int(m[1])
            comment_num = int(m[2])

        blog_info = BlogInfo(recover_file_name(encoded_category),
                             recover_file_name(blog_title),
                             blog_id, comment_num,  read_num)

    return blog_info


def sort_blog_list_by_time(blog_info_list):
    return sorted(blog_info_list,
                  key=lambda blog_info: blog_info.blog_id,
                  reverse=True)
