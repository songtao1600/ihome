# -*- coding: utf-8 -*-
# @Author  :songtao

import logging
import random
import re

from constants import *
from .BaseHandler import BaseHandler
from utils.captcha.captcha import captcha
from utils.response_code import RET
from libs.yuntongxun.SDK.CCP import cpp

class ImageCodeHandler(BaseHandler):
    """
    生成图片验证码
    """
    def get(self, *args, **kwargs):
        code_id = self.get_argument("codeid")
        pre_code_id = self.get_argument("pcodeid")
        if pre_code_id:
            try:
                pre_code_id = "image_code_" + pre_code_id
                self.redis.delete(pre_code_id)
            except Exception as e:
                logging.error(e)
        name, text, image = captcha.generate_captcha()
        try:
            self.redis.setex("image_code_%s" % code_id, IMAGE_CODE_EXPIRES_SECONDS, text)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="保存数据错误"))
        self.set_header("Content-Type", "image/jpg")
        self.write(image)

class SMSCodeHandler(BaseHandler):
    """
    生成手机验证码
    """
    def post(self, *args, **kwargs):
        #获取参数
        mobile = self.json_args.get("mobile")
        image_code_id = self.json_args.get("image_code_id")
        image_code_text = self.json_args.get("image_code_text")

        #校验参数
        if not all((mobile,image_code_id,image_code_text)):
            return self.write(dict(errno = RET.PARAMERR, errmsg = "参数不完整"))
        if not re.match("(^1[3|4|5|7|8]\d{9}$)|(^09\d{8}$)",mobile):
            return self.write(dict(errno=RET.PARAMERR, errmsg="手机号不正确"))

        #判断图片验证码是否正确
        try:
            real_image_code_text = self.redis.get("image_code_%s" %image_code_id).decode()
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno = RET.DBERR, errmsg = "查询错误"))
        if not real_image_code_text:
            return self.write(dict(errno = RET.NODATA, errmsg = "验证码过期"))
        if real_image_code_text.lower() != image_code_text.lower():
            return self.write(dict(errno=RET.DATAERR, errmsg="验证码有误"))

        #生成随机验证码保寸到redis
        sms_code = "%04d" % random.randint(0, 9999)
        # sms_code = "1234"
        try:
            self.redis.setex("sms_code_%s" % mobile, SMS_CODE_EXPIRES_SECONDS, sms_code)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="保存手机验证码错误"))

        #发送短信
        try:
            result = cpp.sendTemplateSMS(mobile, [sms_code, SMS_CODE_EXPIRES_SECONDS], 1)

        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.THIRDERR, errmsg="发送手机验证码失败"))

        # print(result)
        #正常返回
        if result['statusCode'] == '000000':
            return self.write(dict(errno=RET.OK, errmsg="成功"))
        else:
            logging.error(result['statusCode'])
            return self.write(dict(errno=RET.UNKOWNERR, errmsg="失败"))

