# -*- coding: utf-8 -*-
# @Author  :songtao

import logging
import re
import hashlib
import json

from utils.session import Session
from config import *
from constants import *
from utils.response_code import RET
from .BaseHandler import BaseHandler
from utils.common import require_logined

class IndexHandler(BaseHandler):
    '''
    主页信息
    '''
    def get(self, *args, **kwargs):
        try:
            ret = self.redis.get("home_page_data")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            json_houses = json.loads(ret.decode())
        else:
            try:
                # 查询数据库，返回房屋订单数目最多的5条数据(房屋订单通过hi_order_count来表示）
                cur = self.db.cursor()
                cur.execute("select hi_house_id as house_id,hi_title as title,hi_order_count,hi_index_image_url as img_url from ih_house_info " \
                                          "order by hi_order_count desc limit %s;" % HOME_PAGE_MAX_HOUSES)
                houses = cur.fetchall()
            except Exception as e:
                logging.error(e)
                return self.write({"errcode":RET.DBERR, "errmsg":"get data error"})
            if not houses:
                return self.write({"errcode":RET.NODATA, "errmsg":"no data"})
            # print(houses)
            for house in houses:
                if not house["img_url"]:
                    continue
                house['img_url'] = iamage_base_url + house['img_url']

            json_houses = houses
            #     house = {
            #         "house_id":l["hi_house_id"],
            #         "title":l["hi_title"],
            #         "img_url": iamage_base_url + l["hi_index_image_url"]
            #     }
            #     houses.append(house)
            # json_houses = json.dumps(houses)
            try:
                self.redis.setex("home_page_data", HOME_PAGE_DATA_REDIS_EXPIRE_SECOND, json.dumps(json_houses))
            except Exception as e:
                logging.error(e)

        # 返回首页城区数据
        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            json_areas = json.loads(ret.decode())
        else:
            try:
                cur = self.db.cursor()
                cur.execute("select ai_area_id as area_id,ai_name as name from ih_area_info")
                area_ret = cur.fetchall()
            except Exception as e:
                logging.error(e)
                area_ret = None
            # areas = []
            # if area_ret:
            #     for area in area_ret:
            #         areas.append(dict(area_id=area["ai_area_id"], name=area["ai_name"]))
            json_areas = area_ret

            try:
                self.redis.setex("area_info", REDIS_AREA_INFO_EXPIRES_SECONDES, json.dumps(json_areas))
            except Exception as e:
                logging.error(e)
        # resp = '{"errcode":"0", "errmsg":"OK", "houses":%s, "areas":%s}' % (json_houses, json_areas)
        # print(json_areas)
        return self.write(dict(errcode=RET.OK, errmsg="OK", houses=json_houses, areas=json_areas))


class RegisterHandler(BaseHandler):
    """
    用户注册
    """
    def post(self, *args, **kwargs):
        #获取参数
        mobile = self.json_args.get("mobile")
        phonecode = self.json_args.get("phonecode")
        password = self.json_args.get("password")

        #判断参数合法性
        #参数是否为空
        if not all((mobile, phonecode, password)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数不完整"))
        #手机号格式是否正确
        if not re.match("(^1[3|4|5|7|8]\d{9}$)|(^09\d{8}$)",mobile):
            return self.write(dict(errno=RET.PARAMERR, errmsg="手机号格式不正确"))
        #密码长度判断
        if len(password) < 6:
            return self.write(dict(errno=RET.PARAMERR, errmsg="密码长度必须大于6"))
        try:
            real_phone_code = self.redis.get("sms_code_%s" %mobile).decode()
        except Exception as e:
            logging.error("查询sms_code验证码出错")
            return self.write(dict(errcode=RET.DBERR, errmsg="注册失败"))
        if not real_phone_code:
            return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))
        if real_phone_code != phonecode:
            return self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))
        # 判断改手机号是否已经存在
        try:
            cur = self.db.cursor()
        except Exception as e:
            logging.error("创建游标失败",e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="注册失败"))

        sql = "select * from ih_user_profile where up_mobile = %s;" % mobile
        try:
            cur.execute(sql)
            ret = cur.fetchone()
            if ret:
                cur.close()
                return self.write(dict(errcode=RET.DATAEXIST, errmsg="手机号已存在"))
        except Exception as e:
            logging.error("查询数据库错误")
            cur.close()
            # self.db.close()
            return self.write(dict(errcode=RET.DATAERR, errmsg="注册失败"))
        #密码加密
        passwd = hashlib.sha256((password + passwd_hash_key).encode("utf-8")).hexdigest()
        #将用户数据保存到数据库
        sql = "insert into ih_user_profile(up_name, up_mobile, up_passwd) values(%s, %s, '%s');" % (mobile,mobile,passwd)
        try:
            user_id = cur.execute(sql)
            self.db.commit()
            #self.db.close()
        except Exception as e:
            self.db.rollback()
            logging.error(e)
            logging.error("注册失败")
        finally:
            cur.close()
            # self.db.close()
            return self.write(dict(errcode=RET.DATAERR, errmsg="注册失败"))
        # 用session记录用户的登录状态
        # session = Session(self)
        # session["user_id"] = user_id
        # session["mobile"] = mobile
        # session["name"] = mobile
        return self.write(dict(errcode=RET.OK, errmsg="注册成功"))

class LoginHandler(BaseHandler):
    """
    用户登录
    """
    def post(self, *args, **kwargs):
        #获取参数
        mobile = self.json_args.get("mobile")
        password = self.json_args.get("password")
        #判断参数合法性
        if not all((mobile,password)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))
        if not re.match("(^1[3|4|5|7|8]\d{9}$)|(^09\d{8}$)",mobile):
            return self.write(dict(errno=RET.PARAMERR, errmsg="手机号格式不正确"))
        # 从数据库中取出密码
        try:
            cur = self.db.cursor()
        except Exception as e:
            logging.error("创建游标失败",e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="登录失败"))

        sql = "select up_user_id,up_name,up_passwd from ih_user_profile where up_mobile = %s;" % mobile
        try:
            cur.execute(sql)
            req = cur.fetchone()
        except Exception as e:
            logging.error("查询数据库错误", e)
            cur.close()
            #self.db.close()
            return self.write(dict(errcode=RET.DATAERR, errmsg="登录失败"))

        passwd = hashlib.sha256((password + passwd_hash_key).encode("utf-8")).hexdigest()
        if req and req['up_passwd'] == passwd:
            try:
                session = Session(self)
                session["user_id"] = req['up_user_id']
                session["mobile"] = mobile
                session["name"] = req['up_name']
            except Exception as e:
                logging.error(e)
            return self.write(dict(errcode=RET.OK, errmsg="OK"))
        else:
            return self.write(dict(errcode=RET.DATAERR, errmsg="手机号或密码错误！"))

class CheckLoginHandler(BaseHandler):
    """
    判断用户是否登录
    """

    def get(self, *args, **kwargs):
        if self.current_user:
            # name = (json.loads(self.current_user.decode()).get("name"))
            name = self.current_user.get("name")
            self.write({"errcode": RET.OK, "errmsg": "true", "data": {"name": name}})
        else:
            self.write({"errcode": RET.SESSIONERR, "errmsg": "false"})

class LogoutHandler(BaseHandler):
    '''
    退出
    '''
    @require_logined
    def get(self, *args, **kwargs):
        session = Session(self)
        session.clear()
        self.write(dict(errcode=RET.OK, errmsg="退出成功"))






