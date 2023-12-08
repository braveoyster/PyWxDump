import os
from pathlib import PureWindowsPath, Path
import sqlite3

import requests

from parsing import load_chats
import json
from models import Account

# constants
OUTPUT_DIR = 'decrypt_dbs'


def upload_data(wx_info, user_root, local_info):
    wxid = wx_info['wxid']
    contacts = get_sync_concats(wxid, local_info)

    results = []
    for contact in contacts:
        print(contact)
        # load_test()
        chats = load_chats(wxid, user_root, contact)

        if chats:
            results.append({
                'contact': contact,
                'chats': chats
            })

    sync_results = upload_to_server(wx_info, results)

    return sync_results


def upload_to_server(wxinfo, chats):
    print('uploading to server')
    url = 'http://192.168.20.77:9098/api/chats'
    sync_results = []
    for item in chats:
        data = {
            'wxinfo': wxinfo,
            'chats': item['chats'],
            'contact': item['contact']
        }
        # print(data)
        x = requests.post(url, json=data)
        print(x.status_code)
        print(x.text)
        if x.status_code == 200:
            sync_results.append(True)

    return sync_results


def get_sync_concats(wxid, local_info):
    # 聊天记录写入有一定缓存时间，开始时间往期buf20分钟
    begin_time = local_info.lastSyncTime / 999 - (20 * 60 * 1000) if local_info else 0
    micro_msg_db_path = os.path.join(OUTPUT_DIR, wxid, 'MicroMsg.db')
    db = sqlite3.connect(micro_msg_db_path)
    cursor = db.cursor()

    sql = f'SELECT c.UserName, Alias, NickName, Type, Remark FROM Contact c JOIN ChatInfo ci ON c.UserName = ci.Username WHERE Type <> 3 AND ci.LastReadedCreateTime > {begin_time} AND c.UserName NOT LIKE \'@chatroom%\';'

    cursor.execute(sql)
    result = cursor.fetchall()
    contacts = []
    for con in result:
        username, alias, nickname, _type, remark = con
        row_data = {"username": username, "nickname": nickname, "remark": remark, "alias": alias,
                    "isChatRoom": username.startswith("@chatroom")}
        contacts.append(row_data)

    cursor.close()
    db.close()

    return contacts
