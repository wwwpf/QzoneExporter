import argparse
import os
from zipfile import ZipFile

from flask import Flask, g, redirect, render_template, url_for

from config import QzoneFileName, QzonePath
from generator import QzoneGenerator
from template_filters_register import register_filters
from tools import test_uin_valid

app = Flask(os.path.splitext(__name__)[0],
            static_folder=os.getcwd(),
            template_folder=QzonePath.HTML_TEMPLATES)
app.config.from_object(__name__)
register_filters(app)
app.config.update(dict(
    SECRET_KEY="1234"
))

download_if_not_exist = False


def global_get(k, default_value):
    if k not in g:
        g.k = default_value
    return g.k


@app.route("/")
def home():
    uins = []
    files = os.listdir(".")
    for f in files:
        if os.path.isdir(f) and test_uin_valid(f):
            uins.append(f)

    return render_template(QzoneFileName.PREVIEW_HTML, uins=uins)


@app.route("/<uin>/")
def uin_home(uin):
    if not test_uin_valid(uin) or not os.path.exists(uin):
        return redirect(url_for("home"))
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_home()


@app.route("/<uin>/shuoshuo/")
def _shuoshuo(uin):
    return redirect(url_for("shuoshuo", uin=uin, page=1))


@app.route("/<uin>/shuoshuo/<int:page>/")
def shuoshuo(uin, page=1):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_shuoshuo(page)


@app.route("/<uin>/msg_board/")
def _msg_board(uin):
    return redirect(url_for("msg_board", uin=uin, page=1))


@app.route("/<uin>/msg_board/<int:page>/")
def msg_board(uin, page=1):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_msg_board(page)


@app.route("/<uin>/blog/")
def blog(uin):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_blog()


@app.route("/<uin>/blog/<encoded_category>/")
def blog_category(uin, encoded_category):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_blog(encoded_category)


@app.route("/<uin>/blog/<encoded_category>/<int:blog_id>/")
def _single_blog(uin, encoded_category, blog_id):
    return redirect(url_for("single_blog", uin=uin,
                            encoded_category=encoded_category,
                            blog_id=blog_id, page=1))


@app.route("/<uin>/blog/<encoded_category>/<int:blog_id>/<int:page>/")
def single_blog(uin, encoded_category, blog_id, page=1):
    generator = global_get(uin, QzoneGenerator(uin))
    return generator.generate_blog(encoded_category, blog_id, page)


@app.route("/<uin>/photo/")
def album(uin):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_photo()


@app.route("/<uin>/photo/<encoded_album>/")
def _photo(uin, encoded_album):
    return redirect(url_for("photo", uin=uin,
                            encoded_album=encoded_album, page=1))


@app.route("/<uin>/photo/<encoded_album>/<int:page>/")
def photo(uin, encoded_album, page=1):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_photo(encoded_album, page)


@app.route("/<uin>/photo/<encoded_album>/<int:page>/dialog_layer/<int:comment_index>")
def dialog_layer(uin, encoded_album, page, comment_index=0):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_dialog_layer(encoded_album, page, comment_index)


@app.route("/<uin>/photo/<encoded_album>/<int:page>/photo_layer/<int:photo_index>")
def photo_layer(uin, encoded_album, page, photo_index=0):
    generator = global_get(uin, QzoneGenerator(uin, download_if_not_exist))
    return generator.generate_photo_layer(encoded_album, page, photo_index)


def main():
    global download_if_not_exist
    parser = argparse.ArgumentParser()

    parser.add_argument("--download",
                        help="当本地不存在图片、视频时，尝试下载至本地",
                        action="store_true")

    args = parser.parse_args()

    download_if_not_exist = args.download

    app.run(debug=True)


if __name__ == "__main__":

    icenter = os.path.join(QzonePath.HTML_STATIC, QzoneFileName.ICENTER_CSS)
    if not os.path.exists(icenter):
        z = ZipFile(os.path.join(
            QzonePath.HTML_STATIC, QzoneFileName.ZIP_FILE))
        z.extractall(QzonePath.HTML_STATIC)

    main()
