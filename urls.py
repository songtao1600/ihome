# -*- coding: utf-8 -*-
# @Author  :songtao

import os

from config import *
from handlers import Passport, VerifyCode, Profile, House, Orders
from handlers.BaseHandler import StaticFileHandler

handlers=[
        (r"/api/index", Passport.IndexHandler),
        (r"/api/register", Passport.RegisterHandler),
        (r"/api/login", Passport.LoginHandler),
        (r"/api/logout", Passport.LogoutHandler),
        (r"/api/check_login", Passport.CheckLoginHandler),
        (r"/api/profile", Profile.ProfileHandler),
        (r"/api/profile/avatar", Profile.AvatarHandler),
        (r"/api/profile/name", Profile.NameHandler),
        (r"/api/profile/auth", Profile.AuthHandler),
        (r"/api/house/area", House.AreaInfoHandler),
        (r"/api/house/my", House.MyHousesHandler),
        (r"/api/house/info", House.HouseInfoHandler),
        (r"/api/house/image", House.HouseImageHandler),
        (r"/api/house/list", House.HouseListHandler),
        (r"/api/order", Orders.OrderHandler),
        (r"/api/order/my", Orders.MyOrdersHanlder),
        (r"/api/order/accept", Orders.AcceptOrderHanlder),
        (r"/api/order/comment", Orders.OrderCommentHandler),
        (r"/api/order/reject", Orders.RejectOrderHandler),
        (r"/api/imagecode", VerifyCode.ImageCodeHandler),
        (r"/api/smscode", VerifyCode.SMSCodeHandler),
        (r"/(.*)",StaticFileHandler, dict(path = os.path.join(BASEPATH,"html"),default_filename = "index.html"))
    ]
