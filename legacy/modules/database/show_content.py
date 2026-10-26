# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         Export.py
# Description:  读取聊天记录数据库，存放到集合中返回
# Author:       Zephyrtoria
# Date:         2024/11/18
# -------------------------------------------------------------------------------

import sqlite3
import os


def read_msg_to_list_or_dict(number = 10):
    db_file = "output\\Multi\\"
    listdir = os.listdir(db_file)
    """
    读取 .db 文件内容，并将其存储为列表或字典。

    :param db_file: 数据库文件路径
    :return: 一个字典，每个键是表名，值是该表的数据（以列表或字典形式）。
    """
    # 连接到数据库
    conn = sqlite3.connect(db_file + listdir[0])
    cursor = conn.cursor()

    # 获取所有表名
    # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # tables = cursor.fetchall()
    table_name = "MSG"
    data = {}  # 存储所有表数据

    # 查询表的所有数据
    sql = f"SELECT StrTalker, StrContent, datetime(CreateTime, 'unixepoch', 'localtime') FROM {table_name} WHERE StrTalker not like '%@chatroom' and Type = 1 limit " + str(number)
    cursor.execute(sql)
    rows = cursor.fetchall()

    # 获取表的列名
    # cursor.execute(f"PRAGMA table_info({table_name});")
    columns = ["StrTalker", "StrContent", "CreateTime"]

    # 将数据存储为字典列表
    table_data = [dict(zip(columns, row)) for row in rows]
    data[table_name] = table_data

    # 关闭数据库连接
    conn.close()

    return data
