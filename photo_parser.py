import os

from config import QzoneFileName, QzonePath
from download import Downloader
from media_info import (export_media_url, extract_media_info_from_photo,
                        write_media_info)
from saver import Saver
from tools import logging_wrap, purge_file_name


class AlbumListInfo(Saver):
    def __init__(self, json_data, directory):
        Saver.__init__(self, json_data, directory, QzonePath.PHOTO)

    def export(self):
        self.save(QzoneFileName.PHOTO_ALBUM_INFO)


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
    def __init__(self, json_data, begin, end, directory, album_dir, account_info):
        Saver.__init__(self, json_data, os.path.join(
            directory, QzonePath.PHOTO), album_dir)
        self._filename = "comment_%05d-%05d.json" % (begin, end - 1)

        self._account_info = account_info

    @logging_wrap
    def export(self):
        self.save(self._filename)

        for comment in self.json_data["data"]["comments"]:
            commenter_id = str(comment["poster"]["id"])
            # 当评论id与登录id不一致时导出可能存在的图片url
            if commenter_id != self._account_info.self_uin:
                export_media_url(comment, self.directory_path)


class PhotoParser(Saver):
    def __init__(self, json_data, begin, end, directory, album_dir, float_view=False):
        Saver.__init__(self, json_data, os.path.join(
            directory, QzonePath.PHOTO), album_dir)

        self._download_dir = os.path.join(
            self.directory_path, QzonePath.DOWNLOAD)
        self._float_view = float_view
        filename = "photo_%05d-%05d.json" if not float_view else "floatview_photo_%05d-%05d.json"
        self._filename = filename % (begin, end - 1)
        self._photo_key = "photoList" if not float_view else "photos"
        self._id_key = "lloc" if not float_view else "picKey"

    @logging_wrap
    def export(self):
        self.save(self._filename)

        if not self._float_view:
            return

        # 导出相片url
        media_info_list = []
        if self._photo_key in self.json_data["data"]:
            for photo in self.json_data["data"][self._photo_key]:
                media_info = extract_media_info_from_photo(photo, self._id_key)
                media_info_list.append(media_info)
        write_media_info(media_info_list, self._download_dir,
                         os.path.join(self.directory_path, "..", QzoneFileName.TO_DOWNLOAD))


class PhotoDownloader(Downloader):
    def __init__(self, directory):
        Downloader.__init__(self, QzoneFileName.TO_DOWNLOAD, QzoneFileName.DOWNLOADED,
                            os.path.join(directory, QzonePath.PHOTO))


class PhotoCommentDownloader(Downloader):
    def __init__(self, directory):
        Downloader.__init__(self, QzoneFileName.TO_DOWNLOAD, QzoneFileName.DOWNLOADED,
                            directory)
