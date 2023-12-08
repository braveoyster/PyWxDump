import os
from pathlib import PureWindowsPath, Path
from pywxdump import VERSION_LIST_PATH, VERSION_LIST
from pywxdump.wx_info import read_info
from pywxdump.ui import get_user_list, load_chat_records
import json
from models import Account

# constants
OUTPUT_DIR = 'decrypt_dbs'


def get_info():
    wx_info = read_info(VERSION_LIST)
    print(wx_info)
    if type(wx_info) is str and 'No Run' in wx_info:
        return None

    return wx_info


def get_local_info(wx_info):
    wxid = wx_info['wxid']
    upd = Account.select().where(wxid=wxid)

    return upd


def load_chats(wxid, user_root, contact):
    user = wxid
    msg_all = os.path.join(OUTPUT_DIR, user, 'MSG_all.db')
    media_all = os.path.join(OUTPUT_DIR, user, 'MediaMSG_all.db')
    micro_msg = os.path.join(OUTPUT_DIR, user, 'MicroMsg.db')

    file_store = os.path.join(user_root, 'FileStorage')
    user_list = get_user_list(msg_all, micro_msg)
    username = contact['username']
    chats = []
    try:
        chats = load_chat_records(username, 0, 1000, contact, msg_all, media_all, file_store, user_list)
    except Exception as e:
        print(f'{wxid}的{username}聊天数据解析出现错误，忽略...')
    return chats


def parse_data(users):
    for user, db_path in users.items():
        print(db_path)

        msg_all = os.path.join(OUTPUT_DIR, user, 'MSG_all.db')
        micro_msg = os.path.join(OUTPUT_DIR, user, 'MicroMsg.db')
        media_all = os.path.join(OUTPUT_DIR, user, 'MediaMSG_all.db')
        ps = PureWindowsPath(db_path['Msg'][0])
        ps_obj = Path.joinpath(ps.parents[2], 'FileStorage')
        file_store = str(ps_obj)
        print(file_store)
        contacts = get_user_list(msg_all, micro_msg)
        print(contacts)

        # test user 1
        username = contacts[0]['username']
        chats = load_chat_records(username, 0, 500, contacts[0], msg_all, media_all, file_store, contacts)
        print(chats)
