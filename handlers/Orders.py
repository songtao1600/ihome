# -*- coding: utf-8 -*-
# @Time    :2018/7/12 0012 16:56
# @Author  :songtao
# @File    :Orders.py

import logging
import datetime

from handlers.BaseHandler import BaseHandler
from utils.common import require_logined
from utils.response_code import RET
from config import *

class OrderHandler(BaseHandler):
    """
    订单提交
    """
    @require_logined
    def post(self, *args, **kwargs):
        #获取参数
        user_id = self.session['user_id']
        start_date = self.json_args.get('start_date')
        end_date = self.json_args.get('end_date')
        house_id = self.json_args.get('house_id')
        #参数检查
        if not all((house_id, start_date, end_date)):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "params error"})
        #查询房屋是否存在
        try:
            cur = self.db.cursor()
            cur.execute("select hi_price,hi_user_id from ih_house_info where hi_house_id=%s", (house_id,))
            house = cur.fetchone()
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "get house error"})
        finally:
            cur.close()
        if not house:
            return self.write({"errcode":RET.NODATA, "errmsg":"no data"})
        # 判断预订者是否为房东自己
        if user_id == house['hi_user_id']:
            return self.write({"errcode": RET.ROLEERR, "errmsg": "user is forbidden"})
        # 判断日期是否可以
        # 先转成datetime格式再比较
        days = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.datetime.strptime(start_date,"%Y-%m-%d")).days + 1
        if days <= 0:
            return self.write({"errcode": RET.PARAMERR, "errmsg": "date params error"})

        # 确保用户预订的时间内，房屋没有被别人下单
        try:
            cur = self.db.cursor()
            cur.execute("select count(*) counts from ih_order_info where oi_house_id=%(house_id)s "
                              "and oi_begin_date<%(end_date)s and oi_end_date>%(start_date)s",
                              dict(house_id = house_id, end_date = end_date, start_date = start_date))
            ret = cur.fetchone()
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"get date error"})
        if ret["counts"] > 0:
            return self.write({"errcode":RET.DATAERR, "errmsg":"serve date error"})
        # 总金额
        amount = days * house["hi_price"]
        try:
            cur = self.db.cursor()
            cur.execute("insert into ih_order_info(oi_user_id,oi_house_id,oi_begin_date,oi_end_date,oi_days,oi_house_price,oi_amount)"
                            " values(%(user_id)s,%(house_id)s,%(begin_date)s,%(end_date)s,%(days)s,%(price)s,%(amount)s);",
                        dict(user_id=user_id, house_id=house_id, begin_date=start_date, end_date=end_date, days=days,
                             price=house["hi_price"], amount=amount))
            cur.execute("update ih_house_info set hi_order_count=hi_order_count+1 where hi_house_id=%s;", (house_id,))
            self.db.commit()
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "save data error"})
        finally:
            cur.close()
        return self.write({"errcode": RET.OK, "errmsg": "OK"})

class MyOrdersHanlder(BaseHandler):
    """
    我的订单
    """
    @require_logined
    def get(self, *args, **kwargs):
        user_id = self.session['user_id']

        # 获取用户角色
        role = self.get_argument("role","")
        # 查询房东订单
        if "landlord" == role:
            sql = "select oi_order_id order_id,hi_title title,hi_index_image_url img_url,oi_begin_date start_date,oi_end_date end_date,oi_ctime ctime," \
            "oi_days days,oi_amount amount,oi_status status,oi_comment comment from ih_order_info inner join ih_house_info " \
            "on oi_house_id=hi_house_id where hi_user_id=%s order by oi_ctime desc"
        else:
            sql = "select oi_order_id order_id,hi_title title,hi_index_image_url img_url,oi_begin_date start_date,oi_end_date end_date,oi_ctime ctime," \
                  "oi_days days,oi_amount amount,oi_status status,oi_comment comment from ih_order_info inner join ih_house_info " \
                  "on oi_house_id=hi_house_id where oi_user_id=%s order by oi_ctime desc"

        try:
            cur = self.db.cursor()
            cur.execute(sql,(user_id,))
            orders = cur.fetchall()
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "get data error"})
        finally:
            cur.close()
        if orders:
            for order in orders:
                order['img_url'] = iamage_base_url + order['img_url'] if order['img_url'] else ""
                order['start_date'] = order['start_date'].strftime("%Y-%m-%d")
                order['end_date'] = order['end_date'].strftime("%Y-%m-%d")
                order['ctime'] = order['ctime'].strftime("%Y-%m-%d")
                order['comment'] = order['comment'] if order['comment'] else ""
        return self.write({"errcode": RET.OK, "errmsg": "OK", "orders": orders})

class AcceptOrderHanlder(BaseHandler):
    """
    接单
    """
    @require_logined
    def post(self, *args, **kwargs):
        # 处理的订单编号
        order_id = self.json_args.get("order_id")
        user_id = self.session["user_id"]
        if not order_id:
            return self.write({"errcode": RET.PARAMERR, "errmsg": "params error"})

        try:
            # 确保房东只能修改属于自己房子的订单
            cur = self.db.cursor()
            cur.execute("update ih_order_info set oi_status=3 where oi_order_id=%(order_id)s and oi_house_id in "
                            "(select hi_house_id from ih_house_info where hi_user_id=%(user_id)s) and oi_status=0",
                            # update ih_order_info inner join ih_house_info on oi_house_id=hi_house_id set oi_status=3 where
                            # oi_order_id=%(order_id)s and hi_user_id=%(user_id)s
                            dict(order_id=order_id, user_id=user_id))
            self.db.commit()
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "DB error"})
        finally:
            cur.close()
        self.write({"errcode": RET.OK, "errmsg": "OK"})

class RejectOrderHandler(BaseHandler):
    """
    拒单
    """
    @require_logined
    def post(self, *args, **kwargs):
        user_id = self.session["user_id"]
        order_id = self.json_args.get("order_id")
        reject_reason = self.json_args.get("reject_reason")
        if not all((order_id, reject_reason)):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "params error"})
        try:
            cur = self.db.cursor()
            cur.execute("update ih_order_info set oi_status=6,oi_comment=%(reject_reason)s "
                            "where oi_order_id=%(order_id)s and oi_house_id in (select hi_house_id from ih_house_info "
                            "where hi_user_id=%(user_id)s) and oi_status=0",
                            dict(reject_reason=reject_reason, order_id=order_id, user_id=user_id))
            self.db.commit()
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "DB error"})
        finally:
            cur.close()
        self.write({"errcode": RET.OK, "errmsg": "OK"})

class OrderCommentHandler(BaseHandler):
    """
    评价
    """
    @require_logined
    def post(self, *args, **kwargs):
        user_id = self.session["user_id"]
        order_id = self.json_args.get("order_id")
        comment = self.json_args.get("comment")
        if not all((order_id, comment)):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "params error"})
        try:
            # 需要确保只能评论自己下的订单
            cur = self.db.cursor()
            cur.execute(
                "update ih_order_info set oi_status=4,oi_comment=%(comment)s where oi_order_id=%(order_id)s "
                "and oi_status=3 and oi_user_id=%(user_id)s", dict(comment=comment, order_id=order_id, user_id=user_id))
            self.db.commit()
        except Exception as e:
            cur.close()
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "DB error"})


        # 同步更新redis缓存中关于该房屋的评论信息，此处的策略是直接删除redis缓存中的该房屋数据
        try:
            cur.execute("select oi_house_id from ih_order_info where oi_order_id=%s", (order_id,))
            ret = cur.fetchone()
            if ret:
                self.redis.delete("house_info_%s" % ret["oi_house_id"])
        except Exception as e:
            logging.error(e)
        finally:
            cur.close()
        self.write({"errcode": RET.OK, "errmsg": "OK"})
