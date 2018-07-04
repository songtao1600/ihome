# -*- coding: utf-8 -*-
# @Author  :songtao

import os

from config import *
from handlers import Passport, VerifyCode, Profile
from handlers.BaseHandler import StaticFileHandler

handlers=[
        (r"/index", Passport.IndexHandler),
        (r"/api/register", Passport.RegisterHandler),
        (r"/api/login", Passport.LoginHandler),
        (r"/api/check_login", Passport.CheckLoginHandler),
        (r"/api/profile", Profile.ProfileHandler),
        (r"/api/profile/avatar", Profile.AvatarHandler),
        (r"/api/profile/name", Profile.NameHandler),
        (r"/api/imagecode", VerifyCode.ImageCodeHandler),
        (r"/api/smscode", VerifyCode.SMSCodeHandler),
        (r"/(.*)",StaticFileHandler, dict(path = os.path.join(BASEPATH,"html"),default_filename = "index.html"))
    ]
