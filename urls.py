# -*- coding: utf-8 -*-
# @Author  :songtao

import os

from config import *
from handlers import Passport, VerifyCode, Profile, House
from handlers.BaseHandler import StaticFileHandler

handlers=[
        (r"/index", Passport.IndexHandler), #主页
        (r"/api/register", Passport.RegisterHandler), #注册
        (r"/api/login", Passport.LoginHandler), #登录
        (r"/api/logout", Passport.LogoutHandler), #登录
        (r"/api/check_login", Passport.CheckLoginHandler), #判断登录状态
        (r"/api/profile", Profile.ProfileHandler), #个人信息
        (r"/api/profile/avatar", Profile.AvatarHandler), #上传头像
        (r"/api/profile/name", Profile.NameHandler), #修改用户名
        (r"/api/profile/auth", Profile.AuthHandler), #修改用户名
        (r"/api/house/area", House.AreaInfoHandler), # 城区信息
        (r"/api/house/my", House.MyHousesHandler), # 城区信息
        (r"/api/imagecode", VerifyCode.ImageCodeHandler), #随机图片验证码
        (r"/api/smscode", VerifyCode.SMSCodeHandler), #手机验证码
        (r"/(.*)",StaticFileHandler, dict(path = os.path.join(BASEPATH,"html"),default_filename = "index.html"))
    ]
