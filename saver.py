import json
import os

from tools import logging_wrap


class Saver(object):
    def __init__(self, json_data, dir, sub_dir):
        self._json_data = json_data
        self._directory = os.path.join(dir, sub_dir)
        if not os.path.exists(self._directory):
            os.makedirs(self._directory)

    @property
    def directory_path(self):
        return self._directory

    @property
    def json_data(self):
        return self._json_data

    @logging_wrap
    def save(self, file_name):
        full_file_name = os.path.join(self._directory, file_name)
        with open(full_file_name, "w", encoding="utf-8") as f:
            json.dump(self._json_data, f, indent=4, ensure_ascii=False)

    @logging_wrap
    def export(self):
        print("not implemented")
