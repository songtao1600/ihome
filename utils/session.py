# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :session.py

import uuid
import hashlib
import logging
import json

from config import *
class Session(object):
    def __init__(self, request_handler):
        self.request_handler = request_handler
        self.session_id = self.request_handler.get_secure_cookie("session_id")
        self.data = {}

        # if not self.session_id:
        #     #用户第一次访问
        #     self.session_id = uuid.uuid4().get_hex()
        #     self.session_data = {}
        # else:
        #     try:
        #         self.redis.get(self.session_id)
        #     except Exception as e:
        #         logging.error(e)
        #         self.data = {}
    def get_uuid(self):
        uuid_random = uuid.uuid4().hex
        return uuid_random

    def get_session(self):
        # print(self.session_id)
        return self.request_handler.redis.get(self.session_id)

    def __setitem__(self, key, value):
        if not self.session_id:
            self.session_id = self.get_uuid()

        self.data[key] = value
        json_data = json.dumps(self.data)
        try:
            self.request_handler.redis.setex(self.session_id, SESSION_EXPIRES_SECONDS, json_data)
        except Exception as e:
            logging.error(e)
            raise Exception("save redis error")
        self.request_handler.set_secure_cookie("session_id", self.session_id)

