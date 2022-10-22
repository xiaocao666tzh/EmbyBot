from urllib.parse import unquote
import sys
import telegram, pymysql
import requests
import json
import time
import random
import os

bot = telegram.Bot(token='xxx')
tmdb_api = 'xxx' #Your api key on themoviedb.org
# 连接数据库
connect = pymysql.connect(host='xxx',
                          user='xxx',
                          password='xxx',
                          db='xxx',
                          charset='utf8')  # 服务器名,账户,密码，数据库名称
db = connect.cursor()



itemid = sys.argv[1]
itemname = sys.argv[2]
season_num = sys.argv[3]
episode_num = sys.argv[4]

def get_tmdb_info(api_key=' ',name=' ',season=1,ep=1):
    url = f'https://api.themoviedb.org/3/search/tv?api_key={api_key}&language=zh-CN&page=1&query={name}&include_adult=false'
    r = requests.get(url).json()
    r = r['results'][0]
    tmdb_id = r['id']
    poster_path = r['poster_path']
    ranstr = random.sample('zyxwvutsrqponmlkjihgfedcba',5)
    poster_path_return = f'https://image.tmdb.org/t/p/original{poster_path}'
    os.system(f'wget {poster_path_return} -O a.jpg')
    url = f'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season}/episode/{ep}?api_key={api_key}&language=zh-CN'
    r = requests.get(url).text
    r = json.loads(r)
    if r['overview'] == '':
        overview = '暂时没有介绍呢。'
    else:
        overview = r['overview']
    return r['name'], overview, poster_path_return, tmdb_id

try:
    get_tmdb_inf = get_tmdb_info(api_key=tmdb_api,name=itemname,season=season_num,ep=episode_num)
    ep_name = get_tmdb_inf[0]
    ep_overview = get_tmdb_inf[1]
    poster = get_tmdb_inf[2]
    tmdb_id = get_tmdb_inf[3]
except:
    ep_name = '暂时获取不到呢。'
    ep_overview = '暂时获取不到呢。'
    poster = ''
message = f'#{itemname} #剧集更新\n[订阅更新]您订阅的剧集：{itemname} 更新至 S{season_num}E{episode_num}\n剧集名称：{ep_name}\n剧集简介：{ep_overview}\n<a href="https://www.themoviedb.org/tv/{tmdb_id}"><strong>TMDB</strong></a>'
time.sleep(0.8)
try:
    create_sqli = "SELECT * FROM favorite "
    db.execute(create_sqli)
    result = db.fetchall()
except Exception as e:
    pass
else:
    length = len(result)
    for i in range(length):
        fav_items = result[i][2]
        chatid = result[i][0]
        favs = str(fav_items).split(',')
        fav_length = len(favs)
        for num in range(fav_length):
            if (favs[num] == itemid):
                bot.send_photo(chat_id=chatid,photo=open('./a.jpg', 'rb'),caption=message, parse_mode=telegram.ParseMode.HTML)
                time.sleep(0.8)
                break

