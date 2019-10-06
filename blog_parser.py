import json
import os
import time

from bs4 import BeautifulSoup, Comment

from config import QzonePath
from saver import Saver
from tools import filter_blog_script, logging_wrap, purge_file_name


class BlogCategoryInfo(Saver):
    '''获取日志分类信息
    url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_abs"

    payload = {
        "uin": self._account_info.self_uin,
        "hostUin": self._account_info.target_uin,
        "g_tk": self._account_info.g_tk,
        "blogType": "0",
        "reqInfo": "2"
    }
    '''

    def __init__(self, json_data, dir):
        Saver.__init__(self, json_data, dir, QzonePath.BLOG)

        self._filename = "category_info.json"

        self._cate_info = self.json_data["data"]["cateInfo"]

    @property
    def category_info(self):
        '''返回分类信息

        Returns:
            examples:
            "categoryList": [
                {
                    "category": "个人日记",
                    "cateHex": "b8f6c8cbc8d5bcc7",  # gbk编码
                    "num": 123
                }
            ]
        '''

        return self._cate_info

    def export(self):
        self.save(self._filename)


class BlogsInfo(Saver):
    def __init__(self, json_data, begin, end, directory):
        Saver.__init__(self, json_data, directory, QzonePath.BLOG)

        self._filename = "blogs_%05d-%05d.json" % (begin, end)

    def export(self):
        self.save(self._filename)


class BlogInfo(object):
    def __init__(self, category, title, blog_id, comment_num, read_num=0):
        self._blog_id = blog_id
        self._title = title
        self._category = category
        self._comment_num = comment_num
        self._read_num = read_num

    @property
    def blog_id(self):
        return self._blog_id

    @property
    def title(self):
        return self._title

    @property
    def category(self):
        return self._category

    @property
    def comment_num(self):
        return self._comment_num

    @property
    def read_num(self):
        return self._read_num

    def get_file_name(self):
        return purge_file_name("%s_%s.html" % (self._title, self._blog_id))


class BlogComment(Saver):
    def __init__(self, json_data, begin, end, blog_info, directory):
        Saver.__init__(self, json_data, os.path.join(
            directory, QzonePath.BLOG), purge_file_name(blog_info.category))

        self._filename = "%s_%s_%05d-%05d.json" % (
            blog_info.title, blog_info.blog_id, begin, end - 1)
        self._filename = purge_file_name(self._filename)

    def export(self):
        self.save(self._filename)


class BlogParser(object):
    def __init__(self, directory, blog_info, html_content, read_num=0):
        self._html_content = html_content

        blog_path = os.path.join(
            directory, QzonePath.BLOG, purge_file_name(blog_info.category))
        if not os.path.exists(blog_path):
            os.makedirs(blog_path)
        filename = blog_info.get_file_name()
        self._blog_filename = os.path.join(blog_path, filename)

        self._blog_info = blog_info
        self._read = read_num

        self._bs_obj = BeautifulSoup(self._html_content, "html.parser")

    @logging_wrap
    def export(self):
        with open(self._blog_filename, "w", encoding="utf-8") as f:

            self._bs_obj.title.string = self._blog_info.title

            # 删除script, style标签
            delete_labels = ["script", "style"]
            for delete_label in delete_labels:
                for t in self._bs_obj.find_all(delete_label):
                    if filter_blog_script(t.text):
                        continue
                    t.extract()

            # 删除注释
            for comment in self._bs_obj.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            pubtime = self._bs_obj.find("span", {"id": "pubTime"})
            pubtime.string = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(self._blog_info.blog_id))

            readnum = self._bs_obj.find("span", {"id": "readNum"})
            readnum.string = "阅读(%d)\t评论(%d)" % (
                self._read, self._blog_info.comment_num)

            f.write(self._bs_obj.prettify())
