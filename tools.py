import json
import logging
import os
import random
import re
import time

from config import EXTENSIONS, QzoneKey, QzoneType

escape_chars_map = {' ': '%20', '/': '%2F', '\\': '%5C',
                    ':': '%3A', '*': '%2A', '?': '%3F', '"': '%22',
                    '<': '%3C', '>': '%3E', '|': '%7C'}


def random_sleep(a=3, b=5):
    sleep_time = random.uniform(a, b)
    print("sleep %.2fs" % sleep_time)
    time.sleep(sleep_time)


def match_media_type(filename, media_type):
    '''通过 filename 的扩展名是否为指定的资源类型
    '''

    if not filename or len(filename) == 0:
        return False
    if not media_type:
        return True

    # 暂不处理
    if False and media_type == QzoneType.PICTURE:
        extension = os.path.splitext(filename)[1]
        if len(extension) > 1:
            extension = extension[1:]
            if extension in EXTENSIONS[QzoneType.VIDEO]:
                return False
    return True


def search_file(directory, filename):
    '''搜索并返回 directory 目录中文件名包含 filename 的文件，若不存在返回""
    Args:
        filename: 未编码的文件名
    '''

    if not os.path.exists(directory) or not filename or len(filename) == 0:
        return ""

    filename = purge_file_name(filename)
    files = os.listdir(directory)
    for file in files:
        if filename in file:
            return file
    return ""


def get_max_worker():
    '''获取线程池最多工作线程数量
    '''

    try:
        count = os.cpu_count()
    except:
        count = 1
    return (count << 1) + 1


def logging_wrap(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            logging.exception(e)
    return wrapper


def get_json_data_from_response(resp_text):
    try:
        s = resp_text[resp_text.find("{"): resp_text.rfind("}") + 1]
        return json.loads(s)
    except Exception as e:
        logging.exception(e)
        logging.exception("=====\nto json error: %s\n=====" % resp_text)
        return json.loads("{}")


def filter_string(s):
    if len(s.strip(".")) == 0:
        s = s.replace(".", "%2E")
    return s


def purge_file_name(filename):
    '''编码 filename 中可能含有的非法字符
    '''

    filename = filename.replace("%", "%25")
    filename = filter_string(filename)
    for k, v in escape_chars_map.items():
        filename = filename.replace(k, v)

    return filename


def recover_file_name(filename):
    for k, v in escape_chars_map.items():
        filename = filename.replace(v, k)
    filename = filename.replace("%2E", ".")
    filename = filename.replace("%25", "%")
    return filename


def get_files(directory, match_function):
    '''获取 directory 目录下使 match_function 为真的所有文件 f
    '''

    if not os.path.exists(directory):
        return []
    result = []
    files = os.listdir(directory)
    for f in files:
        if match_function(f):
            result.append(f)
    return result


def test_uin_valid(uin):
    '''判断 uin 是否合法
    '''
    return re.fullmatch(r"\d+", uin)


def test_album_valid(filename):
    '''判断相册名是否合法
    '''
    return re.fullmatch(r"(.+)_(.+)", filename)


def test_blog_info_valid(filename):
    '''判断日志信息文件是否合法
    '''
    return re.fullmatch(r"blogs_\d+-\d+.json", filename)


def test_blog_valid(filename):
    '''判断日志文件名是否合法
    '''
    return re.fullmatch(r"(.+)_(\d+).html", filename)


def test_blog_comment_valid(filename):
    '''判断日志评论文件名是否合法
    '''
    return re.fullmatch(r"((.+)_(\d+))_(\d+)-(\d+).json", filename)


def test_shuoshuo_valid(filename):
    '''判断说说文件名是否合法
    '''
    return re.fullmatch(r"shuoshuo_\d+-\d+.json", filename)


def test_msgboard_valid(filename):
    '''判断留言板文件名是否合法
    '''
    return re.fullmatch(r"msg_board_\d+-\d+.json", filename)


def test_floatview_photo_valid(filename):
    '''判断照片文件名是否合法
    '''
    return re.fullmatch(r"floatview_photo_\d+-\d+.json", filename)


def test_photo_valid(filename):
    '''判断照片文件名是否合法
    '''
    return re.fullmatch(r"photo_\d+-\d+.json", filename)


def test_photo_comment_valid(filename):
    '''判断相册评论文件名是否合法
    '''
    return re.fullmatch(r"comment_\d+-\d+.json", filename)


@logging_wrap
def get_sum_page(files):
    '''前k个文件中的消息数量
    Args:
        files:
            [f1, f2, ..., fn]
            文件 fk 有 ak 条消息
    Returns:
        sum_page:
            {0: 0, 1: s1, 2: s2, ..., n: sn}
            sk = a1 + a2 + ... + ak
    '''

    t = 0
    r = {0: 0}
    for i, f in enumerate(files):
        index = f.rfind("-")
        begin = int(f[f.rfind("_") + 1:index])
        end = int(f[index + 1:f.rfind(".")])
        t += end - begin + 1
        r[i + 1] = t
    return r


def filter_blog_script(script_text):
    key_words = ["var g_oBlogData"]
    for word in key_words:
        if word in script_text:
            return True
    return False


@logging_wrap
def get_album_list_data(album_list_json_data):
    ''' 返回的相册列表根据相册的展示设置在不同的位置中
        普通视图：albumListModeSort，json_data["data"][key]是相册列表
        分类视图：albumListModeClass，(json_data["data"][key]的元素)["albumList"]是相册列表
    '''
    album_list = []
    if QzoneKey.ALBUM_LIST_MODE_SORT_KEY in album_list_json_data:
        album_list = album_list_json_data[QzoneKey.ALBUM_LIST_MODE_SORT_KEY]
    elif QzoneKey.ALBUM_LIST_MODE_CLASS_KEY in album_list_json_data:
        for t in album_list_json_data[QzoneKey.ALBUM_LIST_MODE_CLASS_KEY]:
            if QzoneKey.ALBUM_LIST_KEY in t:
                album_list += t[QzoneKey.ALBUM_LIST_KEY] or []
    return album_list or []
