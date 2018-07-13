# -*- coding: utf-8 -*-
# @Time    :2018/6/14
# @Author  :songtao

import os
import pymysql.cursors

BASEPATH = os.path.dirname(__file__)

SESSION_EXPIRES_SECONDS = 72000 #session失效时间
#Appliaction 配置
settings = {
    'static_path':os.path.join(os.path.dirname(__file__), 'static'),
    'template_path':os.path.join(os.path.dirname(__file__), 'template'),
    'cookie_secret':'ssdsdfdsiwaeijsdcnjiucdsfjkk',
    'xsrf_cookies':True,
    'debug':False,
}

#mysql配置
mysql_options = {
    'host':'172.20.10.11',
    'database':'ihome',
    'user':'username',
    'password':'password',
    'charset':'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}

#redis配置
redis_options = {
    'host':'172.20.10.11',
    'port':6379,
    'socket_timeout':10
}

log_level = 'debug'
log_file = os.path.join(os.path.dirname(__file__), 'logs/log')

# 密码加密密钥
passwd_hash_key = "nlgCjaTXQX2jpupQFQLoQo5N4OkEmkeHsHD9+BBx2WQ="

#七牛url
iamage_base_url = 'http://pb0u3g2h2.bkt.clouddn.com/'
