import os

import config
from saver import Saver
from tools import logging_wrap


class MsgBoardParser(Saver):
    def __init__(self, json_data, begin, end, dir):
        Saver.__init__(self, json_data, dir, config.MSG_BOARD_PATH)

        self._file_name = "msg_board_%05d-%05d.json" % (begin, end - 1)

    def export(self):
        self.save(self._file_name)
