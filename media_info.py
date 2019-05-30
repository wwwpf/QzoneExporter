import logging
import os

from config import MEDIA_TYPE, QzoneFileName, QzoneKey, QzonePath, QzoneType
from tools import logging_wrap


class MediaInfo(object):
    '''资源的相关信息
        type: 
            "video", 视频
            "pic", 图片
        id:
            对应id，如果没有id，用url代替
        url:
            地址
    '''

    def __init__(self, media_type="", media_id="", media_url="", video_thumbnail=""):
        self.type = media_type
        self.id = media_id
        self.url = media_url
        self.video_thumbnail = video_thumbnail


@logging_wrap
def export_media_url(data, directory):
    media_info_list = extract_media_info(data)
    download_dir = os.path.join(directory, QzonePath.DOWNLOAD)
    url_file = os.path.join(directory, QzoneFileName.TO_DOWNLOAD)
    write_media_info(media_info_list, download_dir, url_file)


@logging_wrap
def write_media_info(media_info_list, directory, filename):
    '''将 url 写入 filename，待下载的路径为 directory
    '''

    with open(filename, "a", encoding="utf-8") as f:
        for media_info in media_info_list:
            f.write("%s\t%s\t%s\n" %
                    (media_info.url, directory, media_info.id))


@logging_wrap
def extract_media_info_from_photo(photo, id_key):
    url = ""
    is_video = False
    if photo["is_video"]:
        url = photo["video_info"]["video_url"]
        is_video = True
    else:
        if "raw_upload" in photo and photo["raw_upload"] == 1:
            url = photo["raw"]
        elif "origin" in photo:
            url = photo["origin"]
    if len(url) == 0:
        url = photo["url"]

    media_info = MediaInfo(
        QzoneType.VIDEO if is_video else QzoneType.PICTURE, photo[id_key], url)
    return media_info


@logging_wrap
def extract_media_info(json_data):
    '''提取资源信息
    Returns:
        MediaInfo数组
    '''

    media_info_list = []
    video_thumbnail_url = ""
    for media_type in MEDIA_TYPE:
        if not (media_type in json_data and json_data[media_type]):
            continue
        media_list = json_data[media_type]
        for media in media_list:
            media_url = ""
            media_id = ""
            media_backup = None
            for url_key in QzoneKey.COMMENT_URL:
                if url_key in media and len(media[url_key]) > 0:
                    media_url = media[url_key]
                    media_id = media_url
                    break
            else:
                media_id_key = "%s_id" % media_type
                if media_type == QzoneType.PICTURE\
                        and "is_video" in media and media["is_video"] == 1\
                        and "video_info" in media and media["video_info"]:
                    # 说说正文中同时存在视频与图片
                    media_backup = media
                    media = media["video_info"]
                    media_id_key = "video_id"
                for url_key in QzoneKey.CONTENT_URL:
                    if url_key in media and len(media[url_key]) > 0:
                        media_url = media[url_key]
                        media_id = media[media_id_key]
                        break
                if media_backup:
                    for url_key in QzoneKey.CONTENT_URL:
                        if url_key in media_backup and len(media_backup[url_key]) > 0:
                            video_thumbnail_url = media_backup[url_key]
                            break
            if len(media_url) == 0:
                s = "media url not found in %s" % str(media)
                logging.warning(s)
                continue

            media_info = MediaInfo(
                media_type if not media_backup else QzoneType.VIDEO, media_id, media_url, video_thumbnail_url)
            media_info_list.append(media_info)
    return media_info_list
