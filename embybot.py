import asyncio
from pyrogram import Client, filters
import requests
import json
import string
import pandas as pd
from sqlalchemy import create_engine
import pymysql
import time
import uuid
import random
from datetime import datetime, timedelta



bot_token = "xxx"
db_user = 'xxx'
db_password = 'xxx'
db_name = 'xxx'
bot_name = '@xxx'
api_id = 99999999
api_hash = "xxx"
embyurl = 'xxx'
embyapi = 'xxx'
groupid = -100
channelid = -100
admin_list = [111]
ban_channel_id = -100
line = 'xxx'  # config


app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)  # create tg bot
engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@localhost:3306/{db_name}')
conn = pymysql.connect(host='localhost', user=db_user, password=db_password, database=db_name, port=3306)
cursor = conn.cursor()  # create database connect
pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
pd_config = pd.read_sql_query('select * from config;', engine)
pd_user = pd.read_sql_query('select * from user;', engine)  # setup


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
        df_write.to_sql('invite_code', engine, index=False, if_exists='append')
        return code
    else:
        return 'A'  # not an admin that cannot use this command


async def invite(tgid=0, message=''):
    global pd_user
    global pd_invite_code
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
    if canrig(tgid=tgid) == 'B' or hadname(tgid=tgid) == 'B':
        return 'D'  # have an account or have the chance to register
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
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
        cursor.execute(code_used)  # set the code has been used
        conn.commit()
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
        tgid_find = (pd_user['tgid'] == tgid)
        try:
            tgid = int(pd_user[tgid_find]['tgid'])  # find the tgid if the user is in the databse
        except TypeError:
            df_write = pd.DataFrame({'tgid': tgid, 'admin': 'F', 'canrig': 'T'}, index=[0])
            df_write.to_sql('user', engine, index=False, if_exists='append')  # add the user info
            pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
            pd_user = pd.read_sql_query('select * from user;', engine)
            return 'C'
        setcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='T' WHERE  `tgid`='{tgid}';"
        cursor.execute(setcanrig)  # update the status that can register
        conn.commit()
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
        return 'C'  # done


def canrig(tgid=0):
    global pd_user
    global pd_invite_code
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
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
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
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
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
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
        r = json.loads(r)
        try:
            lastacttime = r['LastActivityDate']
            createdtime = r['DateCreated']
            lastacttime = LocalTime(time=lastacttime)
            createdtime = LocalTime(time=createdtime)
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
            pd_invite_code = pd.read_sql_query('select * from invite_code;',
                                               engine)
            pd_user = pd.read_sql_query('select * from user;', engine)
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
            cursor.execute(setbantime)  # update the status that cannot register
            conn.commit()
            return 'A', emby_name  # Ban the user's emby account
        else:
            if canrig(tgid=replyid):
                setcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`='{replyid}';"
                cursor.execute(setcanrig)  # update the status that cannot register
                conn.commit()
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
            pd_invite_code = pd.read_sql_query('select * from invite_code;',
                                               engine)
            pd_user = pd.read_sql_query('select * from user;', engine)
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
            cursor.execute(setbantime)  # update the status that cannot register
            conn.commit()
            return 'A', emby_name  # Unban the user's emby account
        else:
            return 'C', 'DoNothing'  # do nothing
    else:
        return 'B', 'NotAnAdmin'  # Not an admin


async def create(tgid=0, message=''):  # register with invite code
    global pd_user
    global pd_invite_code
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
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
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
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
        df_write.to_sql('user', engine, index=False,
                        if_exists='append')  # add the user info
        return r['Name'], NewPw
    sqlemby_name = f"UPDATE `{db_name}`.`user` SET `emby_name`='{r['Name']}' WHERE  `tgid`='{tgid}';"
    sqlcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`={tgid};"
    sqlemby_id = f"UPDATE `{db_name}`.`user` SET `emby_id`='{r['Id']}' WHERE  `tgid`='{tgid}';"
    cursor.execute(sqlcanrig)
    cursor.execute(sqlemby_name)
    cursor.execute(sqlemby_id)
    conn.commit()  # write it into database
    pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
    pd_user = pd.read_sql_query('select * from user;', engine)
    return r['Name'], NewPw


async def create_time(tgid=0, message=''):
    global pd_user
    global pd_invite_code
    register_public_time = load_config(config='register_public_time')
    if int(time.time()) < register_public_time:
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
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
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
        tgid_find = (pd_user['tgid'] == tgid)
        tgid_a = (pd_user[tgid_find]['tgid'])
        tgid_a = tgid_a.to_list()
        tgid_find = (pd_user['tgid'] == tgid)
        try:
            tgid_a = int(pd_user[tgid_find]['tgid'])  # find the tgid if the user is in the databse
        except TypeError:
            df_write = pd.DataFrame({'tgid': tgid, 'admin': 'F','emby_name': str(r['Name']), 'emby_id': str(r['Id']), 'canrig': 'F'},index=[0])
            df_write.to_sql('user', engine, index=False,if_exists='append')  # add the user info
            return r['Name'], NewPw
        sqlemby_name = f"UPDATE `{db_name}`.`user` SET `emby_name`='{r['Name']}' WHERE  `tgid`='{tgid}';"
        sqlcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`={tgid};"
        sqlemby_id = f"UPDATE `{db_name}`.`user` SET `emby_id`='{r['Id']}' WHERE  `tgid`='{tgid}';"
        cursor.execute(sqlcanrig)
        cursor.execute(sqlemby_name)
        cursor.execute(sqlemby_id)
        conn.commit()  # write it into database
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
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
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
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
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
        tgid_find = (pd_user['tgid'] == tgid)
        tgid_a = (pd_user[tgid_find]['tgid'])
        tgid_a = tgid_a.to_list()
        tgid_find = (pd_user['tgid'] == tgid)
        try:
            tgid_a = int(pd_user[tgid_find]['tgid'])  # find the tgid if the user is in the databse
        except TypeError:
            df_write = pd.DataFrame({'tgid': tgid, 'admin': 'F', 'emby_name': str(r['Name']), 'emby_id': str(r['Id']), 'canrig': 'F'}, index=[0])
            df_write.to_sql('user', engine, index=False, if_exists='append')  # add the user info
            write_conofig(config='register_public_user',parms=register_public_user - 1)
            return r['Name'], NewPw
        sqlemby_name = f"UPDATE `{db_name}`.`user` SET `emby_name`='{r['Name']}' WHERE  `tgid`='{tgid}';"
        sqlcanrig = f"UPDATE `{db_name}`.`user` SET `canrig`='F' WHERE  `tgid`={tgid};"
        sqlemby_id = f"UPDATE `{db_name}`.`user` SET `emby_id`='{r['Id']}' WHERE  `tgid`='{tgid}';"
        cursor.execute(sqlcanrig)
        cursor.execute(sqlemby_name)
        cursor.execute(sqlemby_id)
        conn.commit()  # write it into database
        pd_invite_code = pd.read_sql_query('select * from invite_code;', engine)
        pd_user = pd.read_sql_query('select * from user;', engine)
        write_conofig(config='register_public_user',parms=register_public_user - 1)
        return r['Name'], NewPw
    else:
        write_conofig(config='register_method', parms='None')
        write_conofig(config='register_public_user',parms=0)
        return 'C'


def load_config(config=''):
    global pd_config
    pd_config = pd.read_sql_query('select * from config;', engine)
    re = pd_config.at[0,config]
    return re


def write_conofig(config='',parms=''):
    code_used = f"UPDATE `{db_name}`.`config` SET `{config}`='{parms}' WHERE  `id`='1';"
    cursor.execute(code_used)
    conn.commit()
    return 'OK'



@app.on_message(filters.text)
async def my_handler(client, message):
    tgid = message.from_user.id
    text = str(message.text)
    if str(text) == '/new_code' or text == f'/new_code{bot_name}':
            re = await CreateCode(tgid=tgid)
            if re == 'A':
                await message.reply('不是管理员请勿使用管理员命令')
            else:
                if IsReply(message=message) == False:
                    await message.reply('邀请码生成成功')
                    await app.send_message(chat_id=tgid, text=f'生成成功，邀请码<code>{re}</code>')
                else:
                    replyid = IsReply(message=message)
                    await message.reply('已为这个用户生成邀请码')
                    await app.send_message(chat_id=replyid, text=f'生成成功，邀请码<code>{re}</code>')
                    await app.send_message(chat_id=tgid, text=f'已为用户<a href="tg://user?id={replyid}">{replyid}</a>生成邀请码，邀请码<code>{re}</code>')
    elif str(text).find('/invite') == 0:
        if prichat(message=message):
            re = await invite(tgid=tgid, message=str(message.text))
            if re == 'A':
                await message.reply('没有找到这个邀请码')
            if re == 'B':
                await message.reply('邀请码已被使用')
            if re == 'C':
                await message.reply('已获得注册资格，邀请码已失效')
            if re == 'D':
                await message.reply('您已有账号或已经获得注册资格，请不要重复使用邀请码')
        else:
            await message.reply('请勿在群组使用该命令')
    elif str(text).find('/create') == 0:
        if str(text) == '/create':
            await message.reply('请输入用户名')

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
                    await message.reply('您已经注册过emby账号，请勿重复注册')
                elif re == 'C':
                    await message.reply('您还未获得注册资格')
                elif re == 'B':
                    await message.reply('请输入用户名，用户名不要包含空格')
                elif re == 'D':
                    await message.reply('该用户名已被使用')
                else:
                    await message.reply(f'创建成功，账号<code>{re[0]}</code>，初始密码为<code>{re[1]}</code>，密码不进行保存，请尽快登陆修改密码')
            else:
                await message.reply('请勿在群组使用该命令')
    elif str(text).find('/register_all_time') == 0:
        re = await register_all_time(tgid=tgid, message=text)
        if re == 'A':
            await message.reply('您不是管理员，请勿随意使用管理命令')
        else:
            expired = time.localtime(re)
            expired = time.strftime("%Y/%m/%d %H:%M:%S", expired)
            await message.reply(f"注册已开放，将在{expired}关闭注册")
    elif str(text) == '/info' or text == f'/info{bot_name}':
        replyid = IsReply(message=message)
        if replyid != False:
            re = userinfo(tgid=replyid)
            if IsAdmin(tgid=tgid):
                if re == 'NotInTheDatabase':
                    await message.reply('用户未入库，无信息')
                elif re[0] == 'HaveAnEmby':
                    await message.reply('用户信息已私发，请查看')
                    await app.send_message(chat_id=tgid, text=f'用户<a href="tg://user?id={replyid}">{replyid}</a>的信息\nEmby Name: {re[1]}\n Emby ID: {re[2]}\n上次活动时间{re[3]}\n账号创建时间{re[4]}\n被ban时间{re[5]}')
                elif re[0] == 'NotHaveAnEmby':
                    await message.reply(f'此用户没有emby账号，可注册：{re[1]}')
            else:
                await message.reply('非管理员请勿随意查看他人信息')
        else:
            re = userinfo(tgid=tgid)
            if re == 'NotInTheDatabase':
                await message.reply('用户未入库，无信息')
            elif re[0] == 'HaveAnEmby':
                await message.reply('用户信息已私发，请查看')
                await app.send_message(chat_id=tgid,
                                       text=f'用户<a href="tg://user?id={tgid}">{tgid}</a>的信息\nEmby Name: {re[1]}\n Emby ID: {re[2]}\n上次活动时间{re[3]}\n账号创建时间{re[4]}\n被ban时间{re[5]}')
            elif re[0] == 'NotHaveAnEmby':
                await message.reply(f'此用户没有emby账号，可注册：{re[1]}')
    elif str(text) == '/help' or str(text) == '/start' or text == f'/start{bot_name}' or text == f'/help{bot_name}':
        await message.reply('用户命令：\n/invite + 邀请码 使用邀请码获取创建账号资格\n/create + 用户名 创建用户（用户名不可包含空格）\n/info 查看用户信息（仅可查看自己的信息）\n/line 查看线路\n/help 输出'
                            '本帮助\n管理命令：\n/new_code 创建新的邀请码 \n/register_all_time + 时间（分）开放注册，时长为指定时间\n/register_all_user + 人数 开放指定数量的注册名额\n/info 回复一位用户，查看他的信息\n/ban_emby 禁用一位用户的Emby账号\n/unban_emby 解禁一位用户的Emby账户')
    elif str(text).find('/register_all_user') == 0:
        re = await register_all_user(tgid=tgid, message=text)
        if re == 'A':
            await message.reply('您不是管理员，请勿随意使用管理命令')
        else:
            await message.reply(f"注册已开放，本次共有{re}个名额")
    elif str(text).find('/ban_emby') == 0:
        if IsReply(message=message) != False:
            replyid = IsReply(message=message)
            re = await BanEmby(tgid=tgid, message=message, replyid=replyid)
            if re[0] == 'A':
                await message.reply(f'用户<a href="tg://user?id={replyid}">{replyid}</a>的Emby账号{re[1]}已被ban')
                await app.send_message(chat_id=ban_channel_id, text=f'#Ban\n用户：<a href="tg://user?id={replyid}">{replyid}</a>\nEmby账号：{re[1]}\n原因：管理员封禁')
            elif re[0] == 'B':
                await message.reply('请勿随意使用管理员命令')
            elif re[0] == 'C':
                await message.reply(f'用户<a href="tg://user?id={replyid}">{replyid}</a>没有Emby账号，但是已经取消了他的注册资格')
            elif re[0] == 'D':
                await message.reply(f'用户<a href="tg://user?id={replyid}">{replyid}</a>没有Emby账号，也没有注册资格')
        else:
            await message.reply('请回复一条消息使用该功能')
    elif str(text).find('/unban_emby') == 0:
        if IsReply(message=message) != False:
            replyid = IsReply(message=message)
            re = await UnbanEmby(tgid=tgid, message=message, replyid=replyid)
            if re[0] == 'A':
                await message.reply(f'用户<a href="tg://user?id={replyid}">{replyid}</a>的Emby账号{re[1]}已解除封禁')
                await app.send_message(chat_id=ban_channel_id, text=f'#Unban\n用户：<a href="tg://user?id={replyid}">{replyid}</a>\nEmby账号：{re[1]}\n原因：管理员解封')
            elif re[0] == 'B':
                await message.reply('请勿随意使用管理员命令')
            elif re[0] == 'C':
                await message.reply(f'用户<a href="tg://user?id={replyid}">{replyid}</a>没有Emby账号，也没有注册资格')
        else:
            await message.reply('请回复一条消息使用该命令')
    elif text == '/line' or text == f'/line{bot_name}':
        if prichat(message=message):
            if hadname(tgid=tgid) == 'B':
                await message.reply(line)
            else:
                await message.reply('无Emby账号无法查看线路')
        else:
            await message.reply('请勿在群组中只用此命令')
    elif text.find('/求片') == 0:
        text = text.split(' ')
        url = text[1]
        name = text[2]
        if url.find('imdb.com') == -1 or url.find('ref') != -1 or url.find('title') == -1
            await message.reply('链接不符合规范')
        else:
            await message.reply('已发送请求')
            await app.send_message(chat_id=ban_channel_id,text=f'#求片\n影片名 #{name}\nIMDB链接：<code>{url}</code>\nTGID <a href="tg://user?id={tgid}">{tgid}</a>')


app.run()
