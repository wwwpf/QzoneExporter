HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    # 获取日志需要 referer 字段，否则返回403。
    "referer": "https://user.qzone.qq.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
}

SHUOSHUO_TID_FILE = "shuoshuo_tid.txt"
SHUOSHUO_PATH = "shuoshuo"

MSG_BOARD_PATH = "msg_board"

BLOG_PATH = "blog"

PHOTO_PATH = "photo"
PHOTO_ALBUM_INFO_FILE = "album_info.json"


DOWNLOAD_PATH = "downloaded"
TO_DOWNLOAD_FILE = "to_download.txt"
DOWNLOADED_FILE = "downloaded.txt"

MEDIA_TYPE = ["video", "pic"]
COMMENT_URL_KEY = ["o_url", "b_url", "hd_url", "s_url"]
CONTENT_URL_KEY = ["url2", "url3"]

RETRY_TIMES = 3
