# -*- coding: utf-8 -*-
# @Author  :songtao

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import pymysql
import redis

from config import *
from tornado.options import options, define
from urls import handlers

define('port', default=8020, type=int)

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.db = pymysql.connect(**mysql_options)

        self.redis = redis.StrictRedis(**redis_options)

def main():
    options.logging = log_level
    options.log_file_prefix = log_file
    tornado.options.parse_command_line()
    # options.logging = "info"

    app = Application(handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    # http_server.bind(options.port)
    # http_server.start(2)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()

