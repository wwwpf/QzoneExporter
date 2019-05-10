import os


class QzoneString(object):
    SHUOSHUO = "说说"
    BLOG = "日志"
    PHOTO = "照片"
    ALBUM = "相册"
    MSGBOARD = "留言板"

    SHUOSHUO_BLOG_ALBUM = "说说和日志相册"


class QzoneFileName(object):
    BASE_HTML = "base.html"
    INDEX_HTML = "index.html"
    PREVIEW_HTML = "preview.html"
    SHUOSHUO_HTML = "shuoshuo.html"
    PHOTO_HTML = "photo.html"
    ALBUM_HTML = "album.html"
    MSG_BOARD_HTML = "msg_board.html"
    BLOG_PREVIEW_HTML = "blog_preview.html"
    SINGLE_BLOG_HTML = "single_blog.html"
    PHOTO_LAYER_HTML = "photo_layer.html"
    DIALOG_LAYER_HTML = "dialog_layer.html"

    PHOTO_ALBUM_INFO = "album_info.json"

    SHUOSHUO_TID = "shuoshuo_tid.txt"
    DOWNLOADED = "downloaded.txt"
    TO_DOWNLOAD = "to_download.txt"

    ICENTER_CSS = "icenter.css"

    ZIP_FILE = "static.zip"


class QzonePath(object):
    HTML = "html"
    HTML_TEMPLATES = os.path.join(HTML, "templates")
    HTML_STATIC = os.path.join(HTML, "static")
    HTML_AVATAR = os.path.join(HTML_STATIC, "avatars")

    SHUOSHUO = "shuoshuo"
    MSG_BOARD = "msg_board"
    BLOG = "blog"
    PHOTO = "photo"

    DOWNLOAD = "downloaded"


class QzoneKey(object):
    COMMENT_URL = ["o_url", "b_url", "hd_url", "s_url"]
    CONTENT_URL = ["url2", "url3"]


class QzoneType(object):
    VIDEO = "video"
    PICTURE = "pic"


MEDIA_TYPE = [QzoneType.VIDEO, QzoneType.PICTURE]

EXTENSIONS = {
    QzoneType.VIDEO: ["mp4"],
    QzoneType.PICTURE: []
}

RETRY_TIMES = 3

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    # 获取日志需要 referer 字段，否则返回 403。
    "referer": "https://user.qzone.qq.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
}
