import asyncio
from pyrogram import Client, filters
import requests
import json
import string
import pandas as pd
from sqlalchemy import create_engine
import time
import uuid
import random
from datetime import datetime, timedelta
from config import *


app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)  # create tg bot
engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
    pool_size=20,
    pool_recycle=3600
)
pd_invite_code = None
pd_config = None
pd_user = None


def db_execute(raw=''):
    if raw == '':
        return

    with engine.connect() as connection:
        result = connection.execute(raw)
        return result


def pd_read_sql_query(raw=''):
    # https://docs.sqlalchemy.org/en/20/core/connections.html#basic-usage
    with engine.connect() as conn:
        return pd.read_sql_query(raw, conn)


def pd_to_sql(df_write, table, **kwargs):
    df_write.to_sql(table, engine, **kwargs)


def IsAdmin(tgid=0):  # TODO change it in database
    for i in range(0, len(admin_list)):
        if tgid == admin_list[i]:
            return True
    return False


def LocalTime(time=''):
    n_LastLogin = time[0:19]
    UTC_FORMAT = "%Y-%m-%dT%H:%M:%S"
    utcTime_LastLogin = datetime.strptime(n_LastLogin, UTC_FORMAT)
    localtime_LastLogin = utcTime_LastLogin + timedelta(hours=8)
    return localtime_LastLogin  # change emby time to Asia/Shanghai time


def IsReply(message=''):
    try:
        tgid = message.reply_to_message.from_user.id
    except AttributeError:
        return False
    return tgid


async def CreateCode(tgid=0):
    if IsAdmin(tgid=tgid):  # If you are a admin, you can create a code
        code = f'register-{str(uuid.uuid4())}'
        df_write = pd.DataFrame({'code': code, 'tgid': tgid, 'time': int(time.time()), 'used': 'F'}, index=[0])
        pd_to_sql(df_write, 'invite_code', index=False, if_exists='append')
        return code
    else:
        return 'A'  # not an admin that cannot use this command


async def invite(tgid=0, message=''):
    global pd_user
    global pd_invite_code
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    if canrig(tgid=tgid) == 'B' or hadname(tgid=tgid) == 'B':
        return 'D'  # have an account or have the chance to register
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    message = message.split(' ')
    code = message[-1]  # get the code
    code_find = (pd_invite_code['code'] == code)
    code = (pd_invite_code[code_find]['code'])
    code = code.to_list()
    try:
        code = code[-1]  # find the code if it is in the database
    except IndexError:
        return 'A'
    used = (pd_invite_code[code_find]['used'])
    used = used.to_list()
    used = used[-1]
    if used == 'T':
        return 'B'  # the code has been used
    else:
        code_used = f"UPDATE `{db_name}`.`invite_code` SET `used`='T' WHERE  `code`='{code}';"
        db_execute(code_used)  # set the code has been used
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        tgid_find = (pd_user['tgid'] == tgid)
        try:
            tgid = int(pd_user[tgid_find]['tgid'])  # find the tgid if the user is in the databse
        except TypeError:
            df_write = pd.DataFrame({'tgid': tgid, 'admin': 'F', 'canrig': 'T'}, index=[0])
            pd_to_sql(df_write, 'user', index=False, if_exists='append')  # add the user info
            pd_invite_code = pd_read_sql_query('select * from invite_code;')
            pd_user = pd_read_sql_query('select * from user;')
            return 'C'
        setcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='T' WHERE  `tgid`='{tgid}';"
        db_execute(setcanrig)  # update the status that can register
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        return 'C'  # done


def canrig(tgid=0):
    global pd_user
    global pd_invite_code
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    tgid_find = (pd_user['tgid'] == tgid)
    tgid = (pd_user[tgid_find]['tgid'])
    tgid = tgid.to_list()
    try:
        tgid = tgid[-1]
    except IndexError:
        return 'A'  # not in the database
    sqlcanrig = (pd_user[tgid_find]['canrig'])
    sqlcanrig = sqlcanrig.to_list()
    sqlcanrig = sqlcanrig[-1]
    sqlemby_name = (pd_user[tgid_find]['emby_name'])
    sqlemby_name = sqlemby_name.to_list()
    sqlemby_name = sqlemby_name[-1]
    if sqlcanrig == 'T':
        return 'B'  # can register
    else:
        return 'C'  # cannot register


def hadname(tgid=0):
    global pd_user
    global pd_invite_code
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    tgid_find = (pd_user['tgid'] == tgid)
    tgid = (pd_user[tgid_find]['tgid'])
    tgid = tgid.to_list()
    try:
        tgid = tgid[-1]
    except IndexError:
        return 'A'  # not in the database
    sqlemby_name = (pd_user[tgid_find]['emby_name'])
    sqlemby_name = sqlemby_name.to_list()
    sqlemby_name = sqlemby_name[-1]
    if sqlemby_name != 'None':
        return 'B'  # have an account
    else:
        return 'C'  # does not have an account

# TODO put the time into the database
async def register_all_time(tgid=0, message=''):  # public register

    if IsAdmin(tgid=tgid):
        message = message.split(' ')
        message = message[-1]
        write_conofig(config='register_public',parms='True')
        write_conofig(config='register_public_time',parms=int(time.time())+(int(message)*60))
        write_conofig(config='register_method', parms='Time')
        return int(time.time())+(int(message)*60)
    else:
        return 'A'  # not an admin

#TODO put the user into the database
async def register_all_user(tgid=0, message=''):
    if IsAdmin(tgid=tgid):
        message = message.split(' ')
        message = message[-1]
        write_conofig(config='register_public', parms='True')
        write_conofig(config='register_public_user',parms=int(message))
        write_conofig(config='register_method', parms='User')
        return int(message)
    else:
        return 'A'  # not an admin


def userinfo(tgid=0):
    global pd_user
    global pd_invite_code
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    tgid_find = (pd_user['tgid'] == tgid)
    tgid_a = (pd_user[tgid_find]['tgid'])
    tgid_a = tgid_a.to_list()
    try:
        tgid = tgid_a[-1]
    except IndexError:
        return 'NotInTheDatabase'
    emby_name = (pd_user[tgid_find]['emby_name'])
    emby_name = emby_name.to_list()
    emby_name = emby_name[-1]
    emby_id = (pd_user[tgid_find]['emby_id'])
    emby_id = emby_id.to_list()
    emby_id = emby_id[-1]
    canrig = (pd_user[tgid_find]['canrig'])
    canrig = canrig.to_list()
    canrig = canrig[-1]
    bantime = (pd_user[tgid_find]['bantime'])
    bantime = bantime.to_list()
    bantime = bantime[-1]
    if bantime == 0:
        bantime = 'None'
    else:
        expired = time.localtime(bantime)
        expired = time.strftime("%Y/%m/%d %H:%M:%S", expired)  # change the time format
        bantime = expired
    if emby_name != 'None':
        r = requests.get(f"{embyurl}/emby/users/{emby_id}?api_key={embyapi}").text
        try:
            r = json.loads(r)
            lastacttime = r['LastActivityDate']
            createdtime = r['DateCreated']
            lastacttime = LocalTime(time=lastacttime)
            createdtime = LocalTime(time=createdtime)
        except json.decoder.JSONDecodeError:
            return 'NotInTheDatabase'
        except KeyError:
            lastacttime = 'None'
            createdtime = 'None'
        return 'HaveAnEmby', emby_name, emby_id, lastacttime, createdtime, bantime
    else:
        return 'NotHaveAnEmby', canrig


def prichat(message=''):
    if str(message.chat.type) == 'ChatType.PRIVATE':
        return True
    else:
        return False


async def BanEmby(tgid=0, message='', replyid=0):
    if IsAdmin(tgid=tgid):
        if hadname(tgid=replyid) == 'B':
            global pd_user
            global pd_invite_code
            pd_invite_code = pd_read_sql_query('select * from invite_code;')
            pd_user = pd_read_sql_query('select * from user;')
            tgid_find = (pd_user['tgid'] == replyid)
            tgid_a = (pd_user[tgid_find]['tgid'])
            tgid_a = tgid_a.to_list()
            try:
                tgid = tgid_a[-1]
            except IndexError:
                return 'NotInTheDatabase'
            emby_name = (pd_user[tgid_find]['emby_name'])
            emby_name = emby_name.to_list()
            emby_name = emby_name[-1]
            emby_id = (pd_user[tgid_find]['emby_id'])
            emby_id = emby_id.to_list()
            emby_id = emby_id[-1]
            params = (('api_key', embyapi),
                      )
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
            }
            data = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":true,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":3}'
            requests.post(embyurl + '/emby/Users/' + emby_id + '/Policy',
                          headers=headers,
                          params=params, data=data)  # update policy
            setbantime = f"UPDATE `{db_name}`.`user` SET `bantime`={int(time.time())} WHERE  `tgid`='{tgid}';"
            db_execute(setbantime)  # update the status that cannot register
            return 'A', emby_name  # Ban the user's emby account
        else:
            if canrig(tgid=replyid):
                setcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`='{replyid}';"
                db_execute(setcanrig)  # update the status that cannot register
                return 'C', 'CannotReg'  # set cannot register
            else:
                return 'D', 'DoNothing'  # do nothing
    else:
        return 'B', 'NotAnAdmin'  # Not an admin


async def UnbanEmby(tgid=0, message='', replyid=0):
    if IsAdmin(tgid=tgid):
        if hadname(tgid=replyid) == 'B':
            global pd_user
            global pd_invite_code
            pd_invite_code = pd_read_sql_query('select * from invite_code;')
            pd_user = pd_read_sql_query('select * from user;')
            tgid_find = (pd_user['tgid'] == replyid)
            tgid_a = (pd_user[tgid_find]['tgid'])
            tgid_a = tgid_a.to_list()
            try:
                tgid = tgid_a[-1]
            except IndexError:
                return 'NotInTheDatabase'
            emby_id = (pd_user[tgid_find]['emby_id'])
            emby_id = emby_id.to_list()
            emby_id = emby_id[-1]
            emby_name = (pd_user[tgid_find]['emby_name'])
            emby_name = emby_name.to_list()
            emby_name = emby_name[-1]
            params = (('api_key', embyapi),
                      )
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
            }
            data = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":3}'
            requests.post(embyurl + '/emby/Users/' + emby_id + '/Policy',
                          headers=headers,
                          params=params, data=data)  # update policy
            setbantime = f"UPDATE `{db_name}`.`user` SET `bantime`={0} WHERE  `tgid`='{tgid}';"
            db_execute(setbantime)  # update the status that cannot register
            return 'A', emby_name  # Unban the user's emby account
        else:
            return 'C', 'DoNothing'  # do nothing
    else:
        return 'B', 'NotAnAdmin'  # Not an admin


async def create(tgid=0, message=''):  # register with invite code
    global pd_user
    global pd_invite_code
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    if hadname(tgid=tgid) == 'B':
        return 'A'  # already have an account
    if canrig(tgid=tgid) != 'B':
        return 'C'  # cannot register
    message = message.split(' ')
    name = message[-1]
    if name == '' or name == ' ':
        return 'B'  # do not input a name
    data = '{"Name":"'+name+'","HasPassword":true}'
    params = (('api_key', embyapi),
              )
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    r = requests.post(url=embyurl+'/emby/Users/New', headers=headers, params=params, data=data).text
    try:
        r = json.loads(r)  # create a new user
    except json.decoder.JSONDecodeError:
        if r.find('already exists.'):
            return 'D'  # already exists
    data1 = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":3}'
    requests.post(embyurl + '/emby/Users/' + r['Id'] + '/Policy', headers=headers,
                  params=params, data=data1)  # update policy
    NewPw = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    data = '{"CurrentPw":"" , "NewPw":"'+NewPw+'","ResetPassword" : false}'
    requests.post(f"{embyurl}/emby/users/{r['Id']}/Password?api_key={embyapi}", headers=headers, data=data)
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    tgid_find = (pd_user['tgid'] == tgid)
    tgid_a = (pd_user[tgid_find]['tgid'])
    tgid_a = tgid_a.to_list()
    tgid_find = (pd_user['tgid'] == tgid)
    try:
        tgid_a = int(pd_user[tgid_find][
                         'tgid'])  # find the tgid if the user is in the databse
    except TypeError:
        df_write = pd.DataFrame(
            {'tgid': tgid, 'admin': 'F', 'emby_name': str(r['Name']),
             'emby_id': str(r['Id']), 'canrig': 'F'}, index=[0])
        pd_to_sql(df_write, 'user', index=False, if_exists='append')  # add the user info
        return r['Name'], NewPw
    sqlemby_name = f"UPDATE `{db_name}`.`user` SET `emby_name`='{r['Name']}' WHERE  `tgid`='{tgid}';"
    sqlcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`={tgid};"
    sqlemby_id = f"UPDATE `{db_name}`.`user` SET `emby_id`='{r['Id']}' WHERE  `tgid`='{tgid}';"
    db_execute(sqlcanrig)
    db_execute(sqlemby_name)
    db_execute(sqlemby_id)
    pd_invite_code = pd_read_sql_query('select * from invite_code;')
    pd_user = pd_read_sql_query('select * from user;')
    return r['Name'], NewPw


async def create_time(tgid=0, message=''):
    global pd_user
    global pd_invite_code
    register_public_time = load_config(config='register_public_time')
    if int(time.time()) < register_public_time:
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        if hadname(tgid=tgid) == 'B':
            return 'A'  # already have an account
        message = message.split(' ')
        name = message[-1]
        if name == '' or name == ' ':
            return 'B'  # do not input a name
        data = '{"Name":"' + name + '","HasPassword":true}'
        params = (('api_key', embyapi),
                  )
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        r = requests.post(url=embyurl + '/emby/Users/New', headers=headers,
                          params=params, data=data).text
        try:
            r = json.loads(r)  # create a new user
        except json.decoder.JSONDecodeError:
            if r.find('already exists.'):
                return 'D'  # already exists
        data1 = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":3}'
        requests.post(embyurl + '/emby/Users/' + r['Id'] + '/Policy',
                      headers=headers,
                      params=params, data=data1)  # update policy
        NewPw = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        data = '{"CurrentPw":"" , "NewPw":"' + NewPw + '","ResetPassword" : false}'
        requests.post(f"{embyurl}/emby/users/{r['Id']}/Password?api_key={embyapi}",
                      headers=headers, data=data)
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        tgid_find = (pd_user['tgid'] == tgid)
        tgid_a = (pd_user[tgid_find]['tgid'])
        tgid_a = tgid_a.to_list()
        tgid_find = (pd_user['tgid'] == tgid)
        try:
            tgid_a = int(pd_user[tgid_find]['tgid'])  # find the tgid if the user is in the databse
        except TypeError:
            df_write = pd.DataFrame({'tgid': tgid, 'admin': 'F','emby_name': str(r['Name']), 'emby_id': str(r['Id']), 'canrig': 'F'},index=[0])
            pd_to_sql(df_write, 'user', index=False, if_exists='append')  # add the user info
            return r['Name'], NewPw
        sqlemby_name = f"UPDATE `{db_name}`.`user` SET `emby_name`='{r['Name']}' WHERE  `tgid`='{tgid}';"
        sqlcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`={tgid};"
        sqlemby_id = f"UPDATE `{db_name}`.`user` SET `emby_id`='{r['Id']}' WHERE  `tgid`='{tgid}';"
        db_execute(sqlcanrig)
        db_execute(sqlemby_name)
        db_execute(sqlemby_id)
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        return r['Name'], NewPw
    else:
        register_method = 'None'
        write_conofig(config='register_method',parms='None')
        write_conofig(config='register_public_time',parms=0)
        return 'C'


async def create_user(tgid=0, message=''):
    global pd_user
    global pd_invite_code
    register_public_user = load_config(config='register_public_user')
    if register_public_user > 0:
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        if hadname(tgid=tgid) == 'B':
            return 'A'  # already have an account
        message = message.split(' ')
        name = message[-1]
        if name == '' or name == ' ':
            return 'B'  # do not input a name
        data = '{"Name":"' + name + '","HasPassword":true}'
        params = (('api_key', embyapi),
                  )
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        r = requests.post(url=embyurl + '/emby/Users/New', headers=headers,
                          params=params, data=data).text
        try:
            r = json.loads(r)  # create a new user
        except json.decoder.JSONDecodeError:
            if r.find('already exists.'):
                return 'D'  # already exists
        data1 = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":3}'
        requests.post(embyurl + '/emby/Users/' + r['Id'] + '/Policy',
                      headers=headers,
                      params=params, data=data1)  # update policy
        NewPw = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        data = '{"CurrentPw":"" , "NewPw":"' + NewPw + '","ResetPassword" : false}'
        requests.post(f"{embyurl}/emby/users/{r['Id']}/Password?api_key={embyapi}",
                      headers=headers, data=data)
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        tgid_find = (pd_user['tgid'] == tgid)
        tgid_a = (pd_user[tgid_find]['tgid'])
        tgid_a = tgid_a.to_list()
        tgid_find = (pd_user['tgid'] == tgid)
        try:
            tgid_a = int(pd_user[tgid_find]['tgid'])  # find the tgid if the user is in the databse
        except TypeError:
            df_write = pd.DataFrame({'tgid': tgid, 'admin': 'F', 'emby_name': str(r['Name']), 'emby_id': str(r['Id']), 'canrig': 'F'}, index=[0])
            pd_to_sql(df_write, 'user', index=False, if_exists='append')  # add the user info
            write_conofig(config='register_public_user',parms=register_public_user - 1)
            return r['Name'], NewPw
        sqlemby_name = f"UPDATE `{db_name}`.`user` SET `emby_name`='{r['Name']}' WHERE  `tgid`='{tgid}';"
        sqlcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`={tgid};"
        sqlemby_id = f"UPDATE `{db_name}`.`user` SET `emby_id`='{r['Id']}' WHERE  `tgid`='{tgid}';"
        db_execute(sqlcanrig)
        db_execute(sqlemby_name)
        db_execute(sqlemby_id)
        pd_invite_code = pd_read_sql_query('select * from invite_code;')
        pd_user = pd_read_sql_query('select * from user;')
        write_conofig(config='register_public_user',parms=register_public_user - 1)
        return r['Name'], NewPw
    else:
        write_conofig(config='register_method', parms='None')
        write_conofig(config='register_public_user',parms=0)
        return 'C'


def load_config(config=''):
    global pd_config
    pd_config = pd_read_sql_query('select * from config;')
    re = pd_config.at[0,config]
    return re


def write_conofig(config='',parms=''):
    code_used = f"UPDATE `{db_name}`.`config` SET `{config}`='{parms}' WHERE  `id`='1';"
    db_execute(code_used)
    return 'OK'

def ItemsCount():
    r = requests.get(f'{embyurl}/Items/Counts?api_key={embyapi}').text
    r= json.loads(r)
    MovieCount = r['MovieCount']
    SeriesCount = r['SeriesCount']
    EpisodeCount = r['EpisodeCount']
    return MovieCount,SeriesCount,EpisodeCount



@app.on_message(filters.text)
async def my_handler(client, message):
    tgid = message.from_user.id
    text = str(message.text)
    if str(text) == '/new_code' or text == f'/new_code{bot_name}':
            re = await CreateCode(tgid=tgid)
            if re == 'A':
                await message.reply('??????????????????????????????????????????')
            else:
                if IsReply(message=message) == False:
                    await message.reply('?????????????????????')
                    await app.send_message(chat_id=tgid, text=f'????????????????????????<code>{re}</code>')
                else:
                    replyid = IsReply(message=message)
                    await message.reply('?????????????????????????????????')
                    await app.send_message(chat_id=replyid, text=f'????????????????????????<code>{re}</code>')
                    await app.send_message(chat_id=tgid, text=f'????????????<a href="tg://user?id={replyid}">{replyid}</a>???????????????????????????<code>{re}</code>')
    elif str(text).find('/invite') == 0:
        if prichat(message=message):
            re = await invite(tgid=tgid, message=str(message.text))
            if re == 'A':
                await message.reply('???????????????????????????')
            if re == 'B':
                await message.reply('?????????????????????')
            if re == 'C':
                await message.reply('??????????????????????????????????????????')
            if re == 'D':
                await message.reply('???????????????????????????????????????????????????????????????????????????')
        else:
            await message.reply('??????????????????????????????')
    elif str(text).find('/create') == 0:
        if str(text) == '/create':
            await message.reply('??????????????????')

        elif str(text) == '/create_code':
            pass
        else:
            if prichat(message=message):
                register_method = load_config(config='register_method')
                if register_method == 'None':
                    re = await create(tgid=tgid, message=str(message.text))
                elif register_method == 'User':
                    re = await create_user(tgid=tgid,message=text)
                elif register_method == 'Time':
                    re = await create_time(tgid=tgid,message=text)
                if re == 'A':
                    await message.reply('??????????????????emby???????????????????????????')
                elif re == 'C':
                    await message.reply('???????????????????????????')
                elif re == 'B':
                    await message.reply('????????????????????????????????????????????????')
                elif re == 'D':
                    await message.reply('????????????????????????')
                else:
                    await message.reply(f'?????????????????????<code>{re[0]}</code>??????????????????<code>{re[1]}</code>??????????????????????????????????????????????????????')
            else:
                await message.reply('??????????????????????????????')
    elif str(text).find('/register_all_time') == 0:
        re = await register_all_time(tgid=tgid, message=text)
        if re == 'A':
            await message.reply('???????????????????????????????????????????????????')
        else:
            expired = time.localtime(re)
            expired = time.strftime("%Y/%m/%d %H:%M:%S", expired)
            await message.reply(f"????????????????????????{expired}????????????")
    elif str(text) == '/info' or text == f'/info{bot_name}':
        replyid = IsReply(message=message)
        if replyid != False:
            re = userinfo(tgid=replyid)
            if IsAdmin(tgid=tgid):
                if re == 'NotInTheDatabase':
                    await message.reply('???????????????????????????')
                elif re[0] == 'HaveAnEmby':
                    await message.reply('?????????????????????????????????')
                    await app.send_message(chat_id=tgid, text=f'??????<a href="tg://user?id={replyid}">{replyid}</a>?????????\nEmby Name: {re[1]}\n Emby ID: {re[2]}\n??????????????????{re[3]}\n??????????????????{re[4]}\n???ban??????{re[5]}')
                elif re[0] == 'NotHaveAnEmby':
                    await message.reply(f'???????????????emby?????????????????????{re[1]}')
            else:
                await message.reply('??????????????????????????????????????????')
        else:
            re = userinfo(tgid=tgid)
            if re == 'NotInTheDatabase':
                await message.reply('???????????????????????????')
            elif re[0] == 'HaveAnEmby':
                await message.reply('?????????????????????????????????')
                await app.send_message(chat_id=tgid,
                                       text=f'??????<a href="tg://user?id={tgid}">{tgid}</a>?????????\nEmby Name: {re[1]}\n Emby ID: {re[2]}\n??????????????????{re[3]}\n??????????????????{re[4]}\n???ban??????{re[5]}')
            elif re[0] == 'NotHaveAnEmby':
                await message.reply(f'???????????????emby?????????????????????{re[1]}')
    elif str(text) == '/help' or str(text) == '/start' or text == f'/start{bot_name}' or text == f'/help{bot_name}':
        await message.reply('???????????????\n/invite + ????????? ???????????????????????????????????????\n/create + ????????? ?????????????????????????????????????????????\n/info ???????????????????????????????????????????????????\n/line ????????????\n/count ??????????????????????????????\n/help ??????'
                            '?????????\n???????????????\n/new_code ????????????????????? \n/register_all_time + ???????????????????????????????????????????????????\n/register_all_user + ?????? ?????????????????????????????????\n/info ???????????????????????????????????????\n/ban_emby ?????????????????????Emby??????\n/unban_emby ?????????????????????Emby??????')
    elif str(text).find('/register_all_user') == 0:
        re = await register_all_user(tgid=tgid, message=text)
        if re == 'A':
            await message.reply('???????????????????????????????????????????????????')
        else:
            await message.reply(f"??????????????????????????????{re}?????????")
    elif str(text).find('/ban_emby') == 0:
        if IsReply(message=message) != False:
            replyid = IsReply(message=message)
            re = await BanEmby(tgid=tgid, message=message, replyid=replyid)
            if re[0] == 'A':
                await message.reply(f'??????<a href="tg://user?id={replyid}">{replyid}</a>???Emby??????{re[1]}??????ban')
                await app.send_message(chat_id=ban_channel_id, text=f'#Ban\n?????????<a href="tg://user?id={replyid}">{replyid}</a>\nEmby?????????{re[1]}\n????????????????????????')
            elif re[0] == 'B':
                await message.reply('?????????????????????????????????')
            elif re[0] == 'C':
                await message.reply(f'??????<a href="tg://user?id={replyid}">{replyid}</a>??????Emby????????????????????????????????????????????????')
            elif re[0] == 'D':
                await message.reply(f'??????<a href="tg://user?id={replyid}">{replyid}</a>??????Emby??????????????????????????????')
        else:
            await message.reply('????????????????????????????????????')
    elif str(text).find('/unban_emby') == 0:
        if IsReply(message=message) != False:
            replyid = IsReply(message=message)
            re = await UnbanEmby(tgid=tgid, message=message, replyid=replyid)
            if re[0] == 'A':
                await message.reply(f'??????<a href="tg://user?id={replyid}">{replyid}</a>???Emby??????{re[1]}???????????????')
                await app.send_message(chat_id=ban_channel_id, text=f'#Unban\n?????????<a href="tg://user?id={replyid}">{replyid}</a>\nEmby?????????{re[1]}\n????????????????????????')
            elif re[0] == 'B':
                await message.reply('?????????????????????????????????')
            elif re[0] == 'C':
                await message.reply(f'??????<a href="tg://user?id={replyid}">{replyid}</a>??????Emby??????????????????????????????')
        else:
            await message.reply('????????????????????????????????????')
    elif text == '/line' or text == f'/line{bot_name}':
        if prichat(message=message):
            if hadname(tgid=tgid) == 'B':
                await message.reply(line)
            else:
                await message.reply('???Emby????????????????????????')
        else:
            await message.reply('?????????????????????????????????')
    elif text.find('/??????') == 0:
        text = text.split(' ')
        url = text[1]
        name = text[2]
        if url.find('imdb.com') == -1 or url.find('ref') != -1 or url.find('title') == -1:
            await message.reply('?????????????????????')
        else:
            await message.reply('???????????????')
            await app.send_message(chat_id=ban_channel_id,text=f'#??????\n????????? #{name}\nIMDB?????????<code>{url}</code>\nTGID <a href="tg://user?id={tgid}">{tgid}</a>')
    elif text == '/count' or text == f'/count{bot_name}':
        re = ItemsCount()
        await message.reply(f'???????????????????{re[0]}\n??????????????????????{re[1]}\n???????????????????{re[2]}')


app.run()
