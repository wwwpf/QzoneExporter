import json
import os

from tools import logging_wrap


class Saver(object):
    def __init__(self, json_data, directory, sub_dir):
        self._json_data = json_data
        self._directory = os.path.join(directory, sub_dir)
        if not os.path.exists(self._directory):
            os.makedirs(self._directory)

    @property
    def directory_path(self):
        return self._directory

    @property
    def json_data(self):
        return self._json_data

    @logging_wrap
    def save(self, filename):
        full_filename = os.path.join(self._directory, filename)
        with open(full_filename, "w", encoding="utf-8") as f:
            json.dump(self._json_data, f, indent=4, ensure_ascii=False)

    @logging_wrap
    def export(self):
        print("not implemented")
