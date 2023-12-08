import datetime
import os
import shutil
import time
from pywxdump import VERSION_LIST, merge_media_msg_db
from pywxdump.wx_info import read_info, get_wechat_db, batch_decrypt, merge_msg_db, merge_copy_db, decrypt

from models import Account
from parsing import parse_data
from upload import upload_data

# constants
OUTPUT_DIR = 'decrypt_dbs'


def get_info():
    wx_info = read_info(VERSION_LIST)
    print(wx_info)
    if type(wx_info) is str and 'No Run' in wx_info:
        return None

    return wx_info


def get_local_info(wx_info):
    if wx_info is None:
        return None

    wxid = wx_info['wxid']
    upd = Account.select().where(Account.wxid == wxid).get_or_none()

    return upd


def exec_sync(wx_info):
    key = wx_info['key']
    wxid = wx_info['wxid']
    file_path = wx_info['filePath']
    acc = wx_info['account']

    decrypt_result = run_decrypt(key, wxid, file_path)

    if not decrypt_result or not decrypt_result[0]:
        print(f'解析{acc}用户失败')
        return False

    user_root = decrypt_result[1]

    print(f'解析{acc}用户的db成功，开始读取数据上传...')

    local_info = get_local_info(wx_info)

    upload_result = upload_data(wx_info, user_root, local_info)

    if upload_result:
        update_sync_info(wx_info)

    return upload_result

    # parse_data(suc_users)

    # results = []
    # for user, db_path in wx_db.items():
    #     print(user)
    #     print(db_path['Msg'])
    #     print(type(db_path))
    #     print('-----')
    #     user_dir = os.path.join(output_path, user)
    #
    #     if not os.path.exists(user_dir):
    #         os.makedirs(user_dir)
    #
    #     result = batch_decrypt(key, db_path, user_dir)
    #     print(result)
    #     print('decrypt result')
    #     results.append(result)
    #
    # print(results)

    # return result

def update_sync_info(wx_info):
    wxid = wx_info['wxid']
    entry = Account.get_or_none(Account.wxid == wxid)

    account = wx_info['account']
    if entry is None:
        Account.create(wxid=wxid, account=account, lastSyncTimeda=int(round(time.time() * 1000)))
    else:
        sync_time = int(round(time.time() * 1000))
        Account.update(lastSyncTime=sync_time).where(Account.wxid == wxid).execute()

    return True


def run_decrypt(keys, wxid, file_path):
    if isinstance(keys, str):
        keys = [keys]

    needed_dbs = ["MicroMsg", "MSG", "MediaMSG", "Sns"]
    user_dbs = get_wechat_db(needed_dbs, None, wxid)

    results = None
    for user, db_path in user_dbs.items():
        ret = decrypt_merge_dbs(db_path, keys, wxid)
        results = (ret, user)

    return results


def all_decrypt(keys, paths, decrypted_path):
    decrypted_paths = []

    for key in keys:
        for path in paths:

            name = os.path.basename(path)  # 文件名
            dtp = os.path.join(decrypted_path, name)  # 解密后的路径
            ret = decrypt(key, path, dtp)
            if not ret or 'Error' in ret:
                break
            decrypted_paths.append(dtp)
        else:  # for循环正常结束，没有break
            break  # 跳出while循环
    else:
        return False  # while循环正常结束，没有break 解密失败
    return decrypted_paths


def decrypt_merge_dbs(db_path, keys, wxid):
    MicroMsgPaths = db_path["MicroMsg"]
    MsgPaths = db_path["MSG"]
    MediaMSGPaths = db_path["MediaMSG"]
    SnsPaths = db_path["Sns"]

    decrypted_path_tmp = os.path.join(OUTPUT_DIR, wxid, "tmp")  # 解密后的目录
    if not os.path.exists(decrypted_path_tmp):
        os.makedirs(decrypted_path_tmp)

    MicroMsgDecryptPaths = all_decrypt(keys, MicroMsgPaths, decrypted_path_tmp)
    MsgDecryptPaths = all_decrypt(keys, MsgPaths, decrypted_path_tmp)
    MediaMSGDecryptPaths = all_decrypt(keys, MediaMSGPaths, decrypted_path_tmp)
    SnsDecryptPaths = all_decrypt(keys, SnsPaths, decrypted_path_tmp)

    # 合并数据库
    decrypted_path = os.path.join(OUTPUT_DIR, wxid)  # 解密后的目录
    MicroMsgDbPath = os.path.join(decrypted_path, "MicroMsg.db")
    MsgDbPath = os.path.join(decrypted_path, "MSG_all.db")
    MediaMSGDbPath = os.path.join(decrypted_path, "MediaMSG_all.db")
    SnsDbPath = os.path.join(decrypted_path, "Sns_all.db")

    if MicroMsgDecryptPaths:
        merge_copy_db(MicroMsgDecryptPaths, MicroMsgDbPath)

    if MsgDecryptPaths:
        merge_msg_db(MsgDecryptPaths, MsgDbPath, 0)

    if MediaMSGDecryptPaths:
        merge_media_msg_db(MediaMSGDecryptPaths, MediaMSGDbPath)

    if SnsDecryptPaths:
        merge_copy_db(SnsDecryptPaths, SnsDbPath)

    shutil.rmtree(decrypted_path_tmp)  # 删除临时目录

    print(f"合并数据库完成：{wxid}, {decrypted_path}")

    return True
