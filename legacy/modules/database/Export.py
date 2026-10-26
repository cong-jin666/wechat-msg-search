# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         Export.py
# Description:  解密当前已经登录的微信账号聊天记录，存放至output文件夹中
# Author:       Zephyrtoria
# Date:         2024/11/18
# -------------------------------------------------------------------------------
import os

from pywxdump import *

class Export:
    output_path = "output"

    def __init__(self):
        dirs = os.listdir(os.getcwd())

        if "output" not in dirs:
            os.mkdir(self.output_path)

        result = self.read_info()

        for each in result:
            if each["key"] is None:
                continue
            input_paths = each["wx_dir"].split("\\")
            input_path = ""
            for i in range(len(input_paths) - 1):
                input_path += input_paths[i] + "\\"

            db_paths = get_wx_db(input_path, ["MSG","MicroMsg"], wxids=each["wxid"])
            db_path = []
            for i in db_paths:
                db_path.append(i["db_path"])
                print(i)

            self.decrypt_db(each["key"], db_path, self.output_path)

    def read_info(self):
        result = get_wx_info(WX_OFFS, is_print=True)  # 读取微信信息
        assert result is not None
        return result

    def decrypt_db(self, key, db_path, out_path):
        return batch_decrypt(key, db_path, out_path, True)
