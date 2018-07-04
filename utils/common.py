# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :common.py

import functools

from utils.response_code import RET

def require_logined(fun):
    """
    用户登录验证装饰器
    :param fun:
    :return:
    """
    @functools.wraps(fun)
    def wapper(request_handler_obj, *args, **kwargs):
        if request_handler_obj.current_user:
            fun(request_handler_obj, *args, **kwargs)
        else:
            return request_handler_obj.write(dict(errcode=RET.SESSIONERR, errmsg="用户未登录"))
    return wapper