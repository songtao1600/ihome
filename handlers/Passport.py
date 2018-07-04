# -*- coding: utf-8 -*-
# @Author  :songtao

import logging
import re
import hashlib
import json
import time

from utils.session import Session
from config import *
from utils.response_code import RET
from .BaseHandler import BaseHandler

class IndexHandler(BaseHandler):
    def get(self, *args, **kwargs):
        return self.render("index.html")

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
            cur.close()
            self.db.close()
        except Exception as e:
            logging.error(e)
            logging.error("注册失败")
            cur.close()
            self.db.close()
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
        print(sql)
        try:
            cur.execute(sql)
            req = cur.fetchone()
        except Exception as e:
            logging.error("查询数据库错误", e)
            cur.close()
            self.db.close()
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






