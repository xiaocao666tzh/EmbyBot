# Emby服管理bot by小草
## 食用教程
### 将项目克隆到本地
```bash
git clone https://github.com/xiaocao666tzh/EmbyBot.git && cd EmbyBot && pip3 install -r requirements.txt
```




### 修改配置文件 config.py.example并重命名为config.py

```
bot_token = "xxx"            您的机器人令牌。从@BotFather获取
db_host = 'localhost'        mysql数据库地址
db_port = 3306               数据库端口
db_user = 'xxx'              数据库用户
db_password = 'xxx'          数据库密码
db_name = 'xxx'              数据库名称
bot_name = '@xxx'            bot username
api_id = 99999999            您的电报 API ID       https://core.telegram.org/api/obtaining_api_id
api_hash = "xxx"             你的 Telegram HASH    https://core.telegram.org/api/obtaining_api_id
embyurl = 'xxx'              emby访问链接          例 https://xxxx.com:8920
embyapi = 'xxx'              进入Emby后台，找到高级-API密钥，生成一个API
groupid = -100               1：转到（https://web.telegram.org）
                             2：转到您的 Gorup 并找到您的 Gorup 链接（https://web.telegram.org/#/im?p=g154513121）
                             3：复制该号码在 g 之后并在此之前放置 (-) -154513121
channelid = -100             只需将消息从您的频道转发到此机器人：( https://telegram.me/getidsbot )
admin_list = [111]           管理员id列表
ban_channel_id = -100 建议和channelid保持一致
line = 'xxx'                 线路
```



### 安装docker
```bash
curl -fsSL get.docker.com -o get-docker.sh && sh get-docker.sh && systemctl enable docker && systemctl start docker
```



### 使用docker创建数据库
```bash
mkdir /root/EmbyBot/mysql

docker run --name tg-mysql -e MYSQL_ROOT_PASSWORD=55566677852 -e MYSQL_ROOT_HOST=% -v /root/EmbyBot/mysql:/var/lib/mysql -p 3306:3306 -d mysql:8 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```



### 创建数据库

#### 使用navicat连接数据库

连接mysql

![](https://dd-static.jd.com/ddimg/jfs/t1/179135/39/28801/28871/63288ddbE7a880590/743d5b36578253f9.png)

#### 创建表格

![](https://dd-static.jd.com/ddimg/jfs/t1/53432/1/21971/13792/63288e26E89be5b9b/1b9d009a1e05933c.png)

#### 导入数据库文件
https://github.com/xiaocao666tzh/EmbyBot/blob/main/embybot.sql.gz

## 启动机器人
前台启动机器人        python3 embybot.py
后台启动机器人        nohup python3 embybot.py > botlog.log 2>&1 &
## 添加进程守护（可选，但强烈建议）
在 /usr/lib/systemd/system 下创建如下文件  
https://github.com/xiaocao666tzh/EmbyBot/blob/main/embybot.service  
PathToEmbybot 改为文件路径  
执行命令  
`systemctl daemon-reload`  
启动bot  
`systemctl start embybot`  
重启bot  
`systemctl restart embybot`  
开机自启  
`systemctl enable embybot`  
停止bot  
`systemctl stop embybot`  
## 使用
发送/start 获取帮助
## 注意
写数据库的时候忘记写完关闭连接了，因此需要设置一个cron任务，每八小时内必须重启一次bot，否则bot会报错！
## 参考
[https://github.com/MisakaF0406/MisakaF_Emby
](https://github.com/MisakaFxxk/MisakaF_Emby)  
## 鸣谢
东东，Misakaf等Emby大佬提供技术支持
Foxcoo 帮我撰写了部分的README


