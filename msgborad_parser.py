
from config import QzonePath
from saver import Saver


class MsgBoardParser(Saver):
    def __init__(self, json_data, begin, end, directory):
        Saver.__init__(self, json_data, directory, QzonePath.MSG_BOARD)

        self._filename = "msg_board_%05d-%05d.json" % (begin, end - 1)

    def export(self):
        self.save(self._filename)
