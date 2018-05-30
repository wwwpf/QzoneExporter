import json
import logging
import random
import time


def random_sleep(a=3, b=5):
    sleep_time = random.uniform(a, b)
    print("sleep %.2fs" % sleep_time)
    time.sleep(sleep_time)


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


def purge_file_name(file_name):
    escape_chars = "/\\:*?\"<>|"
    for c in escape_chars:
        file_name = file_name.replace(c, "%%%X" % ord(c))

    return file_name
