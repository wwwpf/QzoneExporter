#encoding=utf8
import os

import config
from download import Downloader, export_comment_media_url
from saver import Saver
from tools import logging_wrap, purge_file_name


class AlbumListInfo(Saver):
    def __init__(self, json_data, dir):
        Saver.__init__(self, json_data, dir, config.PHOTO_PATH)

    def export(self):
        self.save(config.PHOTO_ALBUM_INFO_FILE)


class AlbumInfo(object):
    def __init__(self, json_data):
        self._json_data = json_data
        self._album_dir = purge_file_name(
            "%s_%s" % (json_data["name"], json_data["id"]))

    @property
    def photo_num(self):
        return self._json_data["total"]

    @property
    def id(self):
        return self._json_data["id"]

    @property
    def name(self):
        return self._json_data["name"]

    @property
    def directory(self):
        return self._album_dir

    def __str__(self):
        return "Album[%s][%s][%dp]" % (self.id, self.name, self.photo_num)


class PhotoComment(Saver):
    def __init__(self, json_data, begin, end, dir, album_dir, account_info):
        Saver.__init__(self, json_data, os.path.join(
            dir, config.PHOTO_PATH), album_dir)
        self._file_name = "comment_%05d-%05d.json" % (begin, end - 1)

        self._account_info = account_info

    @logging_wrap
    def export(self):
        self.save(self._file_name)

        for comment in self.json_data["data"]["comments"]:
            commenter_id = comment["poster"]["id"]
            # 当评论id与登录id不一致时导出可能存在的图片url
            if commenter_id != self._account_info.self_uin:
                export_comment_media_url(
                    comment, os.path.join(self.directory_path, ".."))


class PhotoParser(Saver):
    def __init__(self, json_data, begin, end, dir, album_dir, float_view=False, raw_json_data={}):
        Saver.__init__(self, json_data, os.path.join(
            dir, config.PHOTO_PATH), album_dir)

        self._download_dir = os.path.join(
            self.directory_path, config.DOWNLOAD_PATH)
        self._float_view = float_view
        file_name = "photo_%05d-%05d.json" if not float_view else "floatview_photo_%05d-%05d.json"
        self._file_name = file_name % (begin, end - 1)
        self._photo_key = "photoList" if not float_view else "photos"
        self._id_key = "lloc" if not float_view else "picKey"
        self.raw_json_data = raw_json_data


    def get_exif(self, lloc):
        for i in self.raw_json_data['data']['photoList']:
            if i['lloc'] == lloc:
                return i
        return {}

    @logging_wrap
    def export(self):
        self.save(self._file_name)

        if not self._float_view:
            return
        # 导出相片url
        url_file = os.path.join(os.path.join(
            self.directory_path, ".."), config.TO_DOWNLOAD_FILE)
        with open(url_file, "a", encoding="utf-8") as f:
            if self._photo_key in self.json_data["data"]:
                #import pdb;pdb.set_trace()
                for photo in self.json_data["data"][self._photo_key]:
                    url = ""
                    if photo["is_video"]:
                        url = photo["video_info"]["video_url"]
                    else:
                        if "raw_upload" in photo and photo["raw_upload"] == 1:
                            url = photo["raw"]
                        elif "origin" in photo:
                            url = photo["origin"]
                    if len(url) == 0:
                        url = photo["url"]
                    raw_info = self.get_exif(photo["lloc"])
                    if "exif" not in raw_info:
                        originalTime = ""
                    else:
                        if raw_info["exif"]["originalTime"]:
                            originalTime = raw_info["exif"]["originalTime"]
                        else:
                            originalTime = raw_info["uploadtime"].replace("-", ":")

                    f.write("%s\t%s\t%s\t%s\n" %
                            (url, self._download_dir, photo[self._id_key], originalTime))


class PhotoDownloader(Downloader):
    def __init__(self, dir):
        Downloader.__init__(self, config.TO_DOWNLOAD_FILE, config.DOWNLOADED_FILE,
                            os.path.join(dir, config.PHOTO_PATH))
