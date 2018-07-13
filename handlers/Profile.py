# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :Profile.py

import logging
import json

from utils.common import require_logined, RET
from .BaseHandler import BaseHandler
from utils.image_storage import storage
from config import *

class ProfileHandler(BaseHandler):
    '''
    个人信息
    '''
    @require_logined
    def get(self, *args, **kwargs):
        # session = self.current_user.decode()
        # session = json.loads(session)
        # user_id = session['user_id']
        user_id = self.session['user_id']
        sql = 'select up_name, up_mobile, up_avatar from ih_user_profile where up_user_id = %s' % user_id
        try:
            cur = self.db.cursor()
        except Exception as e:
            logging.error("创建游标失败",e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="获取个人信息失败"))

        try:
            cur.execute(sql)
            req = cur.fetchone()
        except Exception as e:
            logging.error("查询数据库错误", e)
            cur.close()
            #self.db.close()
            return self.write(dict(errcode=RET.DATAERR, errmsg="获取个人信息失败"))

        if req['up_avatar']:
            image_src = iamage_base_url + req['up_avatar']
        else:
            image_src = None
        # print(image_src)
        self.write({"errcode": RET.OK, "errmsg": "OK",
                    "data": {"user_id": user_id, "name": req["up_name"], "mobile": req["up_mobile"],
                             "avatar": image_src}})

class AvatarHandler(BaseHandler):
    """
    上传头像
    """
    @require_logined
    def post(self, *args, **kwargs):
        files = self.request.files.get("avatar")
        if not files:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="未传图片"))
        avatar = files[0]['body']

        #上传头像到七牛
        try:
            file_name = storage(avatar)
        except Exception as e:
            logging('上传头像失败', e)
            return self.write(dict(errcode=RET.PARAMERR, errmsg="上传头像失败"))

        try:
            cur = self.db.cursor()
        except Exception as e:
            logging.error("创建游标失败", e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="上传头像失败"))

        # session = self.current_user.decode()
        # session = json.loads(session)
        # user_id = session['user_id']
        user_id = self.session['user_id']
        sql = 'update ih_user_profile set up_avatar = "%s" where up_user_id = %s' %(file_name, user_id)
        # print(sql)
        try:
            cur.execute(sql)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging('更新头像失败', e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="上传头像失败"))
        finally:
            cur.close()

        self.write(dict(errcode=RET.OK, errmsg="上传成功", data="%s%s" % (iamage_base_url, file_name)))

class NameHandler(BaseHandler):
    """
    更新用户名
    """
    @require_logined
    def post(self, *args, **kwargs):
        name = self.json_args.get("name")
        user_id = self.session['user_id']

        if name in(None,""):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "params error"})

        try:
            cur = self.db.cursor()
        except Exception as e:
            logging.error("创建游标失败", e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="更新姓名失败"))
        sql = "select * from ih_user_profile where up_name = '%s'" % name
        try:
            cur.execute(sql)
            count = cur.fetchone()
            if count:
                cur.close()
                return self.write(dict(errcode=RET.DATAEXIST, errmsg="用户名已存在"))
        except Exception as e:
            cur.close()
            logging.error('查询数据库失败', e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="更新姓名失败"))

        sql = 'update ih_user_profile set up_name = "%s" where up_user_id = %s' % (name, user_id)
        try:
            fet = cur.execute(sql)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging.error('查询数据库失败', e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="更新姓名失败"))
        finally:
            cur.close()

        self.write({"errcode": RET.OK, "errmsg": "OK"})

class AuthHandler(BaseHandler):
    '''
    实名认证
    '''
    @require_logined
    def get(self, *args, **kwargs):
        '''获取信息'''
        user_id = self.session['user_id']

        sql = "select up_real_name,up_id_card from ih_user_profile where up_user_id=%s"
        try:
            cur = self.db.cursor()
            cur.execute(sql, (user_id,))
            auth = cur.fetchone()
            # print(auth)
            cur.close()
            if auth:
                self.write({"errcode": RET.OK, "errmsg": "OK",
                        "data": {"real_name": auth.get("up_real_name", ""), "id_card": auth.get("up_id_card", "")}})
            else:
                return self.write({"errcode": RET.NODATA, "errmsg": "no data"})
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "get data failed"})

    @require_logined
    def post(self, *args, **kwargs):
        '''
        更新实名信息
        :param args:
        :param kwargs:
        :return:
        '''
        real_name = self.json_args.get('real_name')
        id_card = self.json_args.get('id_card')
        user_id = self.session['user_id']
        if real_name in(None,"") or id_card in(None,""):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "params error"})

        #判断身份证格式 --略

        sql = "update ih_user_profile set up_real_name=%s,up_id_card=%s where up_user_id=%s"
        try:
            cur = self.db.cursor()
            cur.execute(sql,(real_name, id_card, user_id))
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "update failed"})
        finally:
            cur.close()

        self.write({"errcode": RET.OK, "errmsg": "OK"})



