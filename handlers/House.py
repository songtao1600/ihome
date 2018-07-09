# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :House.py

import logging
import json

from constants import *
from config import *
from .BaseHandler import BaseHandler
from utils.response_code import RET
from utils.common import require_logined

class AreaInfoHandler(BaseHandler):
    '''
    区域信息
    '''
    def get(self, *args, **kwargs):
        try:
            area_info = self.redis.get("area_info")
        except Exception as e:
            logging.error("获取区域信息失败", e)
            area_info = None
        if area_info:
            area_info = json.loads(area_info.decode())
            # print(type(area_info))
            # print(area_info)
            return self.write(dict(errcode=RET.OK, errmsg="OK", data=area_info))

        sql = 'select ai_area_id,ai_name from ih_area_info; '
        try:
            cur = self.db.cursor()
            cur.execute(sql)
            areas = cur.fetchall()
            # print(type(areas))
            # print(areas)
            self.redis.setex("area_info", REDIS_AREA_INFO_EXPIRES_SECONDES, json.dumps(areas))
            return self.write(dict(errcode=RET.OK, errmsg="OK", data=areas))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询出错"))

class MyHousesHandler(BaseHandler):
    '''
    我的房源
    '''
    @require_logined
    def get(self, *args, **kwargs):
        user_id = self.session['user_id']

        sql = 'select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url ' \
              'from ih_house_info a, ih_area_info b where a.hi_area_id = b.ai_area_id and a.hi_user_id = %s'

        print(sql)
        try:
            cur = self.db.cursor()
            cur.execute(sql,(user_id,))
            my_houses = cur.fetchall()
            houses = []
            for item in my_houses:
                house = {
                    "house_id":item['hi_house_id'],
                    "title": item["hi_title"],
                    "price": item["hi_price"],
                    "ctime": item["hi_ctime"].strftime("%Y-%m-%d"),  # 将返回的Datatime类型格式化为字符串
                    "area_name": item["ai_name"],
                    "img_url":iamage_base_url + item['hi_index_image_url'] if item['hi_index_image_url'] else ""
                }
                houses.append(house)
            return self.write({"errcode":RET.OK, "errmsg":"OK", "houses":houses})
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "get data erro"})






