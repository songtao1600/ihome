# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :House.py

import logging
import json

from constants import *
from .BaseHandler import BaseHandler
from utils.response_code import RET

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
            area_info = area_info.decode()
        if area_info:
            resp = "{'errcode':%s, 'errmsg':'OK', 'data':%s}" %(RET.OK, area_info)
            return self.write(resp)

        sql = 'select ai_area_id,ai_name from ih_area_info; '
        try:
            cur = self.db.cursor()
            cur.execute(sql)
            areas = cur.fetchall()
            # areas = json.dumps(areas)
            # print(areas)
            self.redis.setex("area_info", REDIS_AREA_INFO_EXPIRES_SECONDES, areas)
            self.write(dict(errcode=RET.OK, errmsg="OK", data=areas))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询出错"))







