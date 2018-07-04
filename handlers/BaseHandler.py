# -*- coding: utf-8 -*-
# @Author  :songtao

import json
import tornado.web

from utils.session import Session
from tornado.web import RequestHandler, StaticFileHandler

class BaseHandler(RequestHandler):

    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    def prepare(self):
        self.xsrf_token
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = json.loads(self.request.body.decode('utf-8'))
        else:
            self.json_args = None

    def write_error(self, status_code, **kwargs):
        pass

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def initialize(self):
        pass

    def on_finish(self):
        pass

    def get_current_user(self):
        session = Session(self)
        session_data = session.get_session()
        if session_data:
            self.session = json.loads(session_data.decode())
        else:
            self.session = None
            # self.session = print(self.session)
        # return json.loads(self.session.get_session())
        return self.session

class StaticFileHandler(tornado.web.StaticFileHandler):
    def __init__(self, *args, **kwargs):
        super(StaticFileHandler, self).__init__(*args, **kwargs)





