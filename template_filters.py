import os
import re
from datetime import datetime

from flask import url_for

from config import QzoneFileName, QzonePath
from download import DownloadThread, update_downloaded_file
from media_info import extract_media_info, extract_media_info_from_photo
from tools import logging_wrap, match_media_type, purge_file_name, search_file

AT_PATTERN = re.compile(r"@\{uin:(\d+?),nick:(.+?),.*?\}")
EMOJI_ENCODED_PATTERN = re.compile(r"\[em\](.+?)\[/em\]")
EMOJI_URL_PATTERN = re.compile(r"src=\"(/qzone.+?)\"")
FONT_BACKGROUND_COLOR_PATTERN = re.compile(
    r"\[ffg,(#[0-9A-Fa-f]{6}),(#[0-9A-Fa-f]{6})\](.*?)\[/ft\]", re.DOTALL)
FONT_SHADOW_COLOR_PATTERN = re.compile(
    r"\[ffg,(#[0-9A-Fa-f]{6}),(#[0-9A-Fa-f]{6})\](.*?)\[/ffg\]", re.DOTALL)
FONT_PATTERN = re.compile(
    r"\[ft=(#[0-9A-Fa-f]{6}){0,1},(\d+?){0,1},(.*?){0,1}\](.*?)\[/ft\]", re.DOTALL)
IMG_PATTERN = re.compile(r"\[img\](.*?)\[/img\]")
UIN_NICK_PATTERN = re.compile(r"@{uin:(\d+),nick:(.+?),.*}(.*)", re.DOTALL)
URL_PATTERN = re.compile(r"\[url=(.*?)\](.*?)\[/url\]", re.DOTALL)

CLASS_MAP = {
    1: 'imgscale-big',
    2: 'imgscale-middle',
    3: 'imgscale-small',
    4: 'imgscale-middle',
    5: 'imgscale-small',
    6: 'imgscale-small',
    7: 'imgscale-small',
    8: 'imgscale-small',
    9: 'imgscale-small'
}

ALBUM_PER_ROW = 7
PHOTO_PER_ROW = 6


def extract_nick_uin_content_from_comment(s):
    '''从评论中提取账号、昵称以及回复内容
    '''
    r = {"uin": "", "nick": "", "content": "null"}

    m = UIN_NICK_PATTERN.match(s)
    if m:
        r["uin"] = m[1]
        r["nick"] = m[2]
        r["content"] = m[3]
    else:
        r["content"] = s
    return r


def content_beautify(s):
    '''恢复字符串中可能存在的表情、html 标签、css 样式等
    '''
    while True:
        # 恢复 @用户
        m = AT_PATTERN.search(s)
        if not m:
            break
        s = s.replace(m[0], '<a href="/%s">@%s</a>' % (m[1], m[2]))

    while True:
        # 恢复编码后的表情
        m = EMOJI_ENCODED_PATTERN.search(s)
        if not m:
            break
        s = s.replace(m[0],
                      '<img src="http://qzonestyle.gtimg.cn/qzone/em/%s.gif">' % m[1])

    while True:
        # 恢复 html 格式的表情
        m = EMOJI_URL_PATTERN.search(s)
        if not m:
            break
        s = s.replace(m[1], "http://qzonestyle.gtimg.cn%s" % m[1])

    while True:
        # 恢复 img 标签
        m = IMG_PATTERN.search(s)
        if not m:
            break
        s = s.replace(m[0], '<img src="%s">' % m[1])

    while True:
        # 恢复 a 标签
        m = URL_PATTERN.search(s)
        if not m:
            break
        s = s.replace(m[0], '<a href="%s">%s</a>' % (m[1], m[2]))

    while True:
        # 恢复字体设置
        m = FONT_PATTERN.search(s)
        if not m:
            break
        font_s = "<font "
        font_s += 'color="%s"' % m[1] if m[1] else ""
        font_s += 'size="%s"' % m[2] if m[2] else ""
        font_s += 'face="%s"' % m[3] if m[3] else ""
        font_s += ">%s</font>"
        s = s.replace(m[0], font_s % (m[4]))

    while True:
        # 恢复发光字
        m = FONT_SHADOW_COLOR_PATTERN.search(s)
        if not m:
            break
        shadow = "text-shadow:1px 0 4px %s, 0 1px 4px %s, 0 -1px 4px %s, -1px 0 4px %s;" % (
            m[1], m[1], m[1], m[1])
        color = "color:%s;" % m[2]
        s = s.replace(
            m[0], '<span style="%s %s">%s</span>' % (shadow, color, m[3]))

    while True:
        # 恢复字体颜色
        m = FONT_BACKGROUND_COLOR_PATTERN.search(s)
        if not m:
            break
        s = s.replace(
            m[0], '<span style="color:%s;background-color:%s;">%s</span>' % (m[1], m[2], m[3]))

    return s


def purge_file(file):
    return purge_file_name(file)


def format_datetime(t):
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


def get_media_ids(url):
    '''获取 url 中可能与 id 对应的子串
    '''
    ids = []

    if ".mp4?" in url:
        index1 = url.find("vkey=")
        index2 = url.find("&", index1 + 1)
        return [url[index1:index2]]

    index1 = url.find("?")
    if index1 >= 0:
        index2 = url.find("&", index1 + 1)
        ids.append(url[index1 + 1: index2])

    index1 = url.rfind(",")
    if index1 >= 0:
        ids.append(url[index1 + 1:])

    return ids


@logging_wrap
def serach_photo_todownload_file(photo_directory, filename, media_type=None):
    '''搜索相册中需要下载的文件是否包含 filename，如果有，返回相应url与id
    '''

    to_download_file = os.path.join(photo_directory, QzoneFileName.TO_DOWNLOAD)
    if not os.path.exists(to_download_file):
        return "", ""
    ids = get_media_ids(filename)
    m_id = ""
    with open(to_download_file, "r", encoding="utf-8") as fin:
        for line in fin:
            temp = line.split()
            if len(temp) != 3:
                continue
            media_id = temp[2]
            media_url = temp[0]
            for t in ids:
                if t in media_id or t in media_url:
                    m_id = media_id
                    break
            else:
                continue
            download_dir = temp[1]
            final_filename = search_file(download_dir, media_id)
            if match_media_type(final_filename, media_type):
                full_filename = os.path.join(download_dir, final_filename)
                return url_for("static", filename=full_filename.replace("\\", "/")), media_id
    return "", m_id


@logging_wrap
def search_shuoshuo_media_in_photo(shuoshuo_directory, filename, media_type):
    ''' 搜索相册文件夹中是否存在说说对应文件
    Args:
        shuoshuo_directory: 说说目录
        filename: 文件名
        media_type: 资源类型，图片 or 视频
    '''

    photo_directory = os.path.join(
        shuoshuo_directory, "..", "..", QzonePath.PHOTO)
    return serach_photo_todownload_file(photo_directory, filename, media_type)


@logging_wrap
def search_photo(url, photo_downloaded_dir, **kwargs):
    '''搜索本地相册的图片
    '''
    # 搜索 photo 目录
    r, media_id = "", ""
    photo_directory = os.path.join(photo_downloaded_dir, "..", "..")
    r, media_id = serach_photo_todownload_file(photo_directory, url)
    if len(r) > 0 or len(media_id) > 0:
        return r, media_id
    # 搜索该相册目录
    if kwargs.get("comment", False):
        photo_directory = os.path.join(photo_downloaded_dir, "..")
        r, media_id = serach_photo_todownload_file(photo_directory, url)
    return r, media_id


@logging_wrap
def local_url(directory, filename, has_extension, media_type=None, **kwargs):
    '''判断本地文件是否存在，如果存在则返回相应url以及对应的文件名
    Args:
        filename：待搜索的文件名 或 url
        directory: filename 应存在的目录
        has_extension: filename 是否包含扩展名
        media_type: 指定 filename 的类型：图片、视频等
    Returns:
        url:
            若本地文件存在，返回其url，否则为空
        media_id:
            如果 filename 成功匹配某个待下载的资源，则为其对应 id

    '''

    media_id = ""
    if has_extension:
        full_filename = os.path.join(directory, filename)
        if os.path.exists(full_filename):
            return url_for("static", filename=full_filename.replace("\\", "/")), media_id
    else:
        file = search_file(directory, filename)
        if len(file) > 0:
            full_filename = os.path.join(directory, file)
            return url_for("static", filename=full_filename.replace("\\", "/")), media_id
        if kwargs.get("shuoshuo", False):
            r, media_id = search_shuoshuo_media_in_photo(
                directory, filename, media_type)
            if len(r) > 0:
                return r, media_id
        if kwargs.get("photo", False):
            r, media_id = search_photo(filename, directory, **kwargs)
            if len(r) > 0:
                return r, media_id
    return "", media_id


def get_url(url, directory, filename, filename_has_extension,
            download_if_not_exist=False, downloaded_file=None, media_type=None,
            **kwargs):
    """从本地搜索 url 对应的文件
    搜索成功:
        返回本地地址
    否则:
        若 download_if_not_exist 为 True
            将 url 对应的文件以 filename 保存至 directory，并将 url 写入 downloaded_file
        返回 url
    Args:
        media_type:
            指定资源是图片或视频
        filename:
            未编码的文件名
    """

    l_url, media_id = local_url(directory, filename,
                                filename_has_extension, media_type, **kwargs)
    if len(l_url) > 0:
        return l_url
    if download_if_not_exist:
        if len(media_id) == 0:
            media_id = filename
        download_thread = DownloadThread(url, directory, media_id,
                                         update_downloaded_file,
                                         has_extension=filename_has_extension,
                                         downloaded_file=downloaded_file)
        download_thread.start()
    return url


def get_uin_avatar_url(uin, size=100):
    '''获取指定用户的头像的url
    Args:
        uin: 指定账号
        size: 头像尺寸
    '''

    filename = "%s.%d.png" % (uin, size)
    avatar_url = "http://qlogo3.store.qq.com/qzone/%s/%s/%d" % (
        uin, uin, size)
    return get_url(avatar_url, QzonePath.HTML_AVATAR, filename, True, True)


def get_displayed_page_nums(current, total):
    '''根据当前页计算应该显示的页码，应该显示的页码为首页、末页、当前页以及前后两页
    Args:
        current: 当前页
        total: 总页数
    '''

    r = set(range(current - 2, current + 3)) & set(range(1, total + 1))
    r = r | set([1]) | set([total])
    return sorted(list(r))


def calc_floor(current_index, current_page, sum_page, total_num=0):
    '''计算当前页第 k 条消息在所有消息中的位置，若 total_num 为 0，则第一条位置为 1，否则最后一条位置为1
    Args:
        current_index: 消息在当前页的位置
        current_page: 当前页
        sum_page: 前 k 个页包含的消息条数
        total_num: 所有消息的数量
    '''
    rank = sum_page.get(current_page - 1, 0)
    rank += current_index + 1
    if total_num > 0:
        return total_num - rank + 1
    else:
        return rank


def get_photo_url(url, uin, album_name, album_id, download_if_not_exist=False, comment=False):
    '''获取照片的 url
    '''
    album_dir = purge_file_name("%s_%s" % (album_name, album_id))
    photo_download_dir = os.path.join(uin, QzonePath.PHOTO, album_dir,
                                      QzonePath.DOWNLOAD)
    downloaded_file = os.path.join(
        uin, QzonePath.PHOTO, QzoneFileName.DOWNLOADED)
    u = get_url(url, photo_download_dir, url, False,
                download_if_not_exist, downloaded_file, photo=True, comment=False)
    return u


def get_media_list(json_data, directory, downloaded_file, download_if_not_exist, *args, **kwargs):
    '''获取 json_data 中资源的 url, ID 以及 类型
    '''
    media_info_list = extract_media_info(json_data)
    for media_info in media_info_list:
        media_info.url = get_url(media_info.url, directory, media_info.id,
                                 False, download_if_not_exist, downloaded_file,
                                 media_info.type, *args, **kwargs)
    return media_info_list


@logging_wrap
def get_photo_comment_media_list(json_data, uin, album_name, album_id, download_if_not_exist):
    '''获取相册评论中的资源列表
    '''
    album_dir = purge_file_name("%s_%s" % (album_name, album_id))
    directory = os.path.join(uin, QzonePath.PHOTO,
                             album_dir, QzonePath.DOWNLOAD)
    downloaded_file = os.path.join(
        uin, QzonePath.PHOTO, QzoneFileName.DOWNLOADED)
    return get_media_list(json_data, directory, downloaded_file,
                          download_if_not_exist, photo=True)


def get_shuoshuo_media_list(json_data, uin, download_if_not_exist):
    '''获取说说中的资源列表
    '''
    directory = os.path.join(uin, QzonePath.SHUOSHUO, QzonePath.DOWNLOAD)
    downloaded_file = os.path.join(uin, QzonePath.SHUOSHUO,
                                   QzoneFileName.DOWNLOADED)
    return get_media_list(json_data, directory, downloaded_file,
                          download_if_not_exist, shuoshuo=True)


def album_position_style(n):
    '''计算第 n 个相册的位置
    '''
    i = int(n / ALBUM_PER_ROW)
    j = n % ALBUM_PER_ROW
    return 'style="width:%dpx;height:%dpx;top:%dpx;left:%dpx;"' % (137, 161, i * 211, j * 164)


def photo_position_style(n):
    '''计算第 n 张照片的位置
    '''
    i = int(n / PHOTO_PER_ROW)
    j = n % PHOTO_PER_ROW
    return 'style="width:%dpx;height:auto;top:%dpx;left:%dpx;"' % (177, i * 200, j * 192)


def shuoshuo_media_size(n):
    '''说说的图片数为 n 时，图片的尺寸
    Returns:
        width: 图片宽度
        height: 图片高度
    '''
    w, h = 128, 128
    if n == 1:
        w, h = 400, 300
    elif n == 2 or n == 4:
        w, h = 200, 200
    return {"width": w, "height": h}


def shuoshuo_media_class(n):
    '''说说的图片数为 n 时，img 标签所使用的 class
    '''
    return CLASS_MAP[n]


def matched_comments(photo_id, comments):
    '''搜索 comments 中针对 photo_id 的评论
    '''
    c = []
    for comment in comments:
        if "targetImage" not in comment:
            continue
        if photo_id == comment["targetImage"]["lloc"]:
            c.append(comment)
    return c
