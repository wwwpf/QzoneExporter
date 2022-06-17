import json
import os
import re
import time

import piexif

from tools import purge_file_name, get_album_list_data


def convert(s: str, tag):
    if s == "":
        return s
    elif tag == piexif.TYPES.Ascii:
        return s
    elif tag == piexif.TYPES.Rational or tag == piexif.TYPES.SRational:
        if '/' in s:
            (numerator, denominator) = s.split('/')
            return int(numerator), int(denominator)
        else:
            return int(float(s) * 10000), 10000
    elif tag == piexif.TYPES.Short or tag == piexif.TYPES.Long:
        return int(s)
    elif tag == "GPSPos":
        decimal_degrees = float(s)
        degrees = int(decimal_degrees)
        minutes = int(60 * (decimal_degrees - degrees))
        seconds = int(10000 * (3600 * (decimal_degrees - degrees) - 60 * minutes))
        return (degrees, 1), (minutes, 1), (seconds, 10000)

    return s


class PhotoExifRecover(object):
    def __init__(self, file_dir, floatview_info, raw_info):
        self.file_dir = file_dir
        self.floatview_info = floatview_info
        self.raw_info = raw_info
        self.exif_dict = piexif.load(self.file_dir)
        self.is_dirty = False

    def copy_exif(self, exif_dict_key, exif_value_key, info, info_dict_key, info_value_key, tag=""):
        if exif_value_key in self.exif_dict.setdefault(exif_dict_key, {}):
            return False
        if not info.get(info_dict_key, {}).get(info_value_key, {}):
            return False

        converted = convert(info[info_dict_key][info_value_key], tag)
        self.exif_dict[exif_dict_key][exif_value_key] = converted
        self.is_dirty = True
        print(exif_value_key, " is recovered from ", info_value_key, converted)
        return True

    def coyp_DateTimeOriginal_from_uploadtime(self):  # if originalTime is missing
        if piexif.ExifIFD.DateTimeOriginal in self.exif_dict.setdefault("Exif", {}):
            return

        if not self.raw_info.get("uploadtime"):
            return

        self.exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = self.raw_info["uploadtime"].replace("-", ":")
        self.is_dirty = True
        print(piexif.ExifIFD.DateTimeOriginal, " is recovered from ", "uploadtime")
        return True

    def add_exif(self, exif_dict_key, exif_value_key, value):
        if exif_value_key in self.exif_dict.get(exif_dict_key, {}):
            return
        if not value:
            return

        self.exif_dict.setdefault(exif_dict_key, {})[exif_value_key] = value
        self.is_dirty = True
        print(exif_value_key, " is added as ", value)
        return

    def recover(self):
        print("recovering:", self.file_dir)

        # 0th #
        self.copy_exif("0th", piexif.ImageIFD.Make,
                       self.raw_info, "exif", "make", piexif.TYPES.Ascii)
        self.copy_exif("0th", piexif.ImageIFD.Model,
                       self.raw_info, "exif", "model", piexif.TYPES.Ascii)

        # Exif #
        self.copy_exif("Exif", piexif.ExifIFD.ExposureBiasValue,
                       self.raw_info, "exif", "exposureCompensation", piexif.TYPES.SRational)
        self.copy_exif("Exif", piexif.ExifIFD.ExposureMode,
                       self.raw_info, "exif", "exposureMode", piexif.TYPES.Short)
        self.copy_exif("Exif", piexif.ExifIFD.ExposureProgram,
                       self.raw_info, "exif", "exposureProgram", piexif.TYPES.Short)
        self.copy_exif("Exif", piexif.ExifIFD.ExposureTime,
                       self.raw_info, "exif", "exposureTime", piexif.TYPES.SRational)
        self.copy_exif("Exif", piexif.ExifIFD.Flash,
                       self.raw_info, "exif", "flash", piexif.TYPES.Short)
        self.copy_exif("Exif", piexif.ExifIFD.FNumber,
                       self.raw_info, "exif", "fnumber", piexif.TYPES.Rational)
        self.copy_exif("Exif", piexif.ExifIFD.FocalLength,
                       self.raw_info, "exif", "focalLength", piexif.TYPES.Rational)
        self.copy_exif("Exif", piexif.ExifIFD.ISOSpeed,
                       self.raw_info, "exif", "iso", piexif.TYPES.Long)
        self.copy_exif("Exif", piexif.ExifIFD.LensModel,
                       self.raw_info, "exif", "lensModel", piexif.TYPES.Ascii)
        self.copy_exif("Exif", piexif.ExifIFD.MeteringMode,
                       self.raw_info, "exif", "meteringMode", piexif.TYPES.Short)

        # Exif: OriginalTime #
        if not self.copy_exif("Exif", piexif.ExifIFD.DateTimeOriginal,
                              self.raw_info, "exif", "originalTime", piexif.TYPES.Ascii):
            self.coyp_DateTimeOriginal_from_uploadtime()  # if originalTime is missing

        # GPS #
        if self.copy_exif("GPS", piexif.GPSIFD.GPSLongitude,
                          self.floatview_info, "shootGeo", "pos_x", "GPSPos"):
            # 拍摄地点在东半球是参考东经的；在西半球如参考东经则经度是负数
            self.add_exif("GPS", piexif.GPSIFD.GPSLongitudeRef, "E")
        if self.copy_exif("GPS", piexif.GPSIFD.GPSLatitude,
                          self.floatview_info, "shootGeo", "pos_y", "GPSPos"):
            # 拍摄地点在北半球是参考北纬的；在南半球如参考北纬则维度是负数
            self.add_exif("GPS", piexif.GPSIFD.GPSLatitudeRef, "N")

        if self.is_dirty:
            exif_bytes = piexif.dump(self.exif_dict)
            piexif.insert(exif_bytes, self.file_dir)


class PhotoExifRecoverBatch(object):
    def __init__(self, target_uin):
        self.target_uin = target_uin
        self.e = []

    def batch(self, should_rename=True, should_add_exif=True):
        # re constants
        p_date = re.compile(r"(\d{4})(0[1-9]|1[0-2])(0[1-9]|[1-2]\d|3[0-1])[ _]([0-1]\d|2[0-3])([0-5]\d)([0-5]\d)")
        p_floatview_json = re.compile(r"^floatview_photo_\d{5}-\d{5}.json$")
        p_raw_json = re.compile(r"^photo_\d{5}-\d{5}.json$")

        target_dir = os.path.join(os.getcwd(), self.target_uin, "photo")
        if not os.path.exists(target_dir):
            print("路径不存在，请确认照片已下载，并在本文件尾部添加目标 QQ 号")

        # form album list
        album_info_dir = os.path.join(target_dir, "album_info.json")
        with open(album_info_dir, "r", encoding="utf-8") as album_info_f:
            album_info = json.load(album_info_f)
        album_list = get_album_list_data(album_info['data'])

        # No album at all!
        if len(album_list) <= 0:
            print("【json 记录中无相册！】")
            return

        # do for every album
        for album in album_list:
            album_dir = ""
            files_in_target_dir = os.listdir(target_dir)
            album_id_purged = purge_file_name(album["id"])

            # find album folder
            for file_name_in_target_dir in files_in_target_dir:
                if album_id_purged in file_name_in_target_dir:
                    album_dir = os.path.join(target_dir, file_name_in_target_dir)

                    # rename album folder
                    if should_rename:
                        if not re.search(p_date, file_name_in_target_dir):
                            album_create_timestamp = int(album["createtime"])  # 取相册创建时间
                            album_create_date = time.strftime('%Y%m%d %H%M%S', time.localtime(album_create_timestamp))
                            file_name_in_target_dir_new = album_create_date + " " + file_name_in_target_dir
                            album_dir_new = os.path.join(target_dir, file_name_in_target_dir_new)
                            os.rename(album_dir, album_dir_new)
                            album_dir = album_dir_new

                    break
            if album_dir == "":
                print("相册文件夹缺失:", os.path.join(target_dir, album["name"]))
                continue

            # find floatview and raw json (500+ json文件会分裂。。)
            files_in_album_dir = os.listdir(album_dir)
            floatview_json_dir_list = []
            raw_json_dir_list = []
            for file_name_in_album_dir in files_in_album_dir:
                if re.search(p_floatview_json, file_name_in_album_dir):
                    floatview_json_dir_list.append(os.path.join(album_dir, file_name_in_album_dir))
                elif re.search(p_raw_json, file_name_in_album_dir):
                    raw_json_dir_list.append(os.path.join(album_dir, file_name_in_album_dir))

            # floatview or raw json is missing!
            if len(floatview_json_dir_list) == 0 or len(raw_json_dir_list) == 0:
                print("【相册中照片 json 数据缺失】:", album_dir)
                continue

            floatview_list = []
            raw_list = []
            for floatview_json_dir in floatview_json_dir_list:
                with open(floatview_json_dir, "r", encoding="utf-8") as floatview_json_f:
                    floatview_json = json.load(floatview_json_f)
                    for _floatview_info in floatview_json["data"]["photos"]:
                        floatview_list.append(_floatview_info)
            for raw_json_dir in raw_json_dir_list:
                with open(raw_json_dir, "r", encoding="utf-8") as raw_json_f:
                    raw_json = json.load(raw_json_f)
                    for _raw_info in raw_json["data"]["photoList"]:
                        raw_list.append(_raw_info)

            # find downloaded folder and file list within
            downloaded_dir = os.path.join(album_dir, "downloaded")
            # downloaded folder is missing!
            if not os.path.exists(downloaded_dir):
                print("【无 downloaded 文件夹】:", downloaded_dir)
                continue
            photos_in_album_downloaded_dir = os.listdir(downloaded_dir)

            # start to handle every photo within an album

            # floatview_info
            for floatview_info in floatview_list:
                lloc = floatview_info["lloc"]

                # find raw_info
                raw_info = None
                for _raw_info in raw_list:
                    if _raw_info["lloc"] == lloc:
                        raw_info = _raw_info
                        break

                # find photo_dir
                photo_dir = ""
                lloc_purged = purge_file_name(lloc)
                for photo_name in photos_in_album_downloaded_dir:
                    if lloc_purged in photo_name:
                        photo_dir = os.path.join(downloaded_dir, photo_name)
                        break

                if photo_dir == "":
                    print("照片缺失:", os.path.join(downloaded_dir, lloc_purged))
                    continue

                # recover EXIF
                if should_add_exif:
                    try:
                        photoExifRecover = PhotoExifRecover(photo_dir, floatview_info, raw_info)
                        photoExifRecover.recover()
                    except Exception as e:
                        error_message = "EXIF 写入失败: " + photo_dir + "\n↘失败原因: " + str(e)
                        print(error_message)
                        self.e.append(error_message)
                        continue  # 对于EXIF写入发生异常的文件跳过重命名步骤

                # rename photo
                if should_rename:
                    [dir_name, photo_name] = os.path.split(photo_dir)
                    if not re.search(p_date, photo_name):
                        exif_in_file = piexif.load(photo_dir)
                        if exif_in_file.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal):
                            photo_create_date = \
                                bytes.decode(exif_in_file["Exif"][piexif.ExifIFD.DateTimeOriginal]).replace(":", "")
                            photo_name_new = photo_create_date + " " + photo_name
                            photo_dir_new = os.path.join(dir_name, photo_name_new)
                            os.rename(photo_dir, photo_dir_new)
                            photoExifRecover.file_dir = photo_dir_new

    def show_error_list(self):
        e_count = len(self.e)
        if e_count <= 0:
            print("***EXIF 写入过程未发生异常***")
        else:
            print("***EXIF 写入失败数量：", e_count, "***")
            for e in self.e:
                print(e)


if __name__ == "__main__":
    # 输入
    target_uin = ""  # 此处填入目标QQ号或在运行时输入
    if target_uin == "":
        target_uin = input("请输入要批处理的QQ号: ")
    should_rename = True  # 是否需要将相册和照片文件名前加入时间标识，格式为 "YYYYMMDD HHMMSS 原文件名"，便于排序整理

    photoExifRecoverBatch = PhotoExifRecoverBatch(target_uin)

    # 文件完整性检查
    print("开始文件完整性检查")
    photoExifRecoverBatch.batch(False, False)
    print("***如果照片文件缺失，可单独手动下载，或调整 timeout，重新运行 exporter.py 下载；"
          "\n***如果相册文件夹缺失，请确认是否有空相册。\n")
    input("按回车开始批处理...")

    # 正式批处理
    print("开始批处理")
    photoExifRecoverBatch.batch(should_rename)
    print("批处理完成\n")

    # 异常打印
    input("按回车显示 EXIF 写入异常清单...")
    photoExifRecoverBatch.show_error_list()

# by Yang-z

# Ref
# piexif Documen (piexif库官方文档): https://piexif.readthedocs.io/en/latest/
# official Exif standards(官方Exif标准): http://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf
# 感谢 greysign 将时间写回照片文件的启发: https://github.com/greysign/QzoneExporter.git

# 讲个笑话，我老婆用QQ空间备份照片:(
