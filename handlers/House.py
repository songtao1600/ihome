# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :House.py

import logging
import json
import math

from constants import *
from config import *
from .BaseHandler import BaseHandler
from utils.response_code import RET
from utils.common import require_logined
from utils.image_storage import storage

class AreaInfoHandler(BaseHandler):
    '''
    区域信息
    '''
    def get(self, *args, **kwargs):
        try:
            area_info = self.redis.get("area_info")
        except Exception as e:
            logging.error("获取区域信息失败", e)
            area_info = None
        if area_info:
            area_info = json.loads(area_info.decode())

            return self.write(dict(errcode=RET.OK, errmsg="OK", data=area_info))

        sql = 'select ai_area_id as area_id,ai_name as name from ih_area_info; '
        try:
            cur = self.db.cursor()
            cur.execute(sql)
            areas = cur.fetchall()

            self.redis.setex("area_info", REDIS_AREA_INFO_EXPIRES_SECONDES, json.dumps(areas))
            return self.write(dict(errcode=RET.OK, errmsg="OK", data=areas))
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询出错"))

class MyHousesHandler(BaseHandler):
    '''
    我的房源
    '''
    @require_logined
    def get(self, *args, **kwargs):
        user_id = self.session['user_id']

        sql = 'select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url ' \
              'from ih_house_info a, ih_area_info b where a.hi_area_id = b.ai_area_id and a.hi_user_id = %s'

        try:
            cur = self.db.cursor()
            cur.execute(sql,(user_id,))
            my_houses = cur.fetchall()
            houses = []
            for item in my_houses:
                house = {
                    "house_id":item['hi_house_id'],
                    "title": item["hi_title"],
                    "price": item["hi_price"],
                    "ctime": item["hi_ctime"].strftime("%Y-%m-%d"),  # 将返回的Datatime类型格式化为字符串
                    "area_name": item["ai_name"],
                    "img_url":iamage_base_url + item['hi_index_image_url'] if item['hi_index_image_url'] else ""
                }
                houses.append(house)
            return self.write({"errcode":RET.OK, "errmsg":"OK", "houses":houses})
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "get data erro"})

class HouseInfoHandler(BaseHandler):
    '''
    房屋信息
    '''
    @require_logined
    def post(self, *args, **kwargs):
        '''
        发布新房源
        :param args:
        :param kwargs:
        :return:
        '''
        """{
                    "title":"",
                    "price":"",
                    "area_id":"1",
                    "address":"",
                    "room_count":"",
                    "acreage":"",
                    "unit":"",
                    "capacity":"",
                    "beds":"",
                    "deposit":"",
                    "min_days":"",
                    "max_days":"",
                    "facility":["7","8"]
                }"""
        title = self.json_args.get('title')
        price = self.json_args.get('price')
        area_id = self.json_args.get('area_id')
        address = self.json_args.get('address')
        room_count = self.json_args.get('room_count')
        acreage = self.json_args.get('acreage')
        unit = self.json_args.get('unit')
        capacity = self.json_args.get('capacity')
        beds = self.json_args.get('beds')
        deposit = self.json_args.get('deposit')
        min_days = self.json_args.get('min_days')
        max_days = self.json_args.get('max_days')
        facility = self.json_args.get('facility')
        user_id = self.session['user_id']

        try:
            price = int(price) * 100
            deposit = int(deposit) * 100
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))

        if not all((title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days,
                    max_days, facility)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))

        try:
            sql = "insert into ih_house_info (hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count," \
                  "hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days)" \
                  "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            cur = self.db.cursor()
            cur.execute(sql, (user_id, title, price, area_id, address,
                                       room_count, acreage, unit, capacity,
                                       beds, deposit, min_days, max_days))
            cur.execute("SELECT LAST_INSERT_ID();")
            house_id = cur.fetchone()['LAST_INSERT_ID()']
        except Exception as e:
            self.db.rollback()
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="save data error"))

        try:
            sql = "insert into ih_house_facility(hf_house_id,hf_facility_id) VALUES(%s, %s)"
            vals = []
            for facility_id in facility:
                val = (house_id, facility_id)
                vals.append(val)
            # print(sql)
            logging.debug(vals)
            logging.debug(sql)
            cur.executemany(sql, vals)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging.error(e)
            try:
                cur.execute("delete from ih_house_info where hi_house_id=%s", house_id)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="delete fail"))
            else:
                return self.write(dict(errcode=RET.DBERR, errmsg="no data save"))
        finally:
            cur.close()
        # 返回
        self.write(dict(errcode=RET.OK, errmsg="OK", house_id=house_id))

    def get(self, *args, **kwargs):
        '''
        获取房屋信息
        :param args:
        :param kwargs:
        :return:
        '''

        user_id = self.current_user['user_id']
        house_id = self.get_argument('house_id')

        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))

        #从redis中取房屋信息
        try:
            houses = self.redis.get("house_info_%s" % house_id)
            if houses:
                house_info = json.loads(houses.decode())
                return self.write(dict(errcode=RET.OK, errmsg="OK", data=house_info, user_id=user_id))
        except Exception as e:
            logging.error(e)

        #从数据库中取房屋信息
        sql = "select hi_title as title,hi_price as price,hi_address as address ,hi_room_count as room_count," \
              "hi_acreage as acreage,hi_house_unit as unit,hi_capacity as capacity,hi_beds as beds," \
              "hi_deposit as deposit,hi_min_days as min_days,hi_max_days as max_days,up_name as user_name," \
              "up_avatar as user_avatar,hi_user_id as user_id " \
              "from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id where hi_house_id=%s"
        try:
            cur = self.db.cursor()
            cur.execute(sql, (house_id,))
            house_info = cur.fetchone()
        except Exception as e:
            return self.write(dict(errcode=RET.DBERR, errmsg="查询错误"))
        if not house_info:
            return self.write(dict(errcode=RET.NODATA, errmsg="查无此房"))
        house_info['hid'] = house_id
        house_info['user_avatar'] = iamage_base_url + house_info['up_avatar'] if house_info.get("up_avatar") else ""
        # print(house_info)
        #查询房屋图片
        sql = "select hi_url from ih_house_image where hi_house_id=%s"
        try:
            cur.execute(sql,(house_id,))
            house_imgs = cur.fetchall()
        except Exception as e:
            logging.error(e)
            house_imgs = None
        images = []
        if house_imgs:
            for img in house_imgs:
                images.append(iamage_base_url + img['hi_url'])
        # print("images", images)
        house_info['images'] = images

        #查询房屋设施
        sql = "select hf_facility_id from ih_house_facility where hf_house_id=%s"
        try:
            cur.execute(sql,(house_id,))
            facility = cur.fetchall()
        except Exception as e:
            logging.error(e)
            facility = None
        fac_list=[]
        for fac in facility:
            fac_list.append(fac['hf_facility_id'])
        # print("facility",fac_list)
        house_info['facilities'] = fac_list

        #查询评论信息
        sql = "select oi_comment as content, up_name as user_name,date_format(oi_utime,'%%Y-%%m-%%d %%H:%%i:%%S') as ctime,up_mobile from ih_order_info inner join ih_user_profile " \
              "on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"
        try:
            cur.execute(sql,(house_id,))
            order = cur.fetchall()
        except Exception as e:
            logging.error(e)
            order = None
        # order['ctime'] = order['ctime'].strftime("%Y-%m-%d %H:%M:%S")
        house_info['comments'] = order
        # print(house_info)
        try:
            self.redis.setex("house_info_%s" % house_id, REDIS_HOUSE_INFO_EXPIRES_SECONDES, json.dumps(house_info))
        except Exception as e:
            logging.error(e)
        return self.write(dict(errcode=RET.OK, errmsg="OK", data=house_info, user_id=user_id))

class HouseImageHandler(BaseHandler):
    '''
    上传房屋图片
    '''
    @require_logined
    def post(self, *args, **kwargs):
        house_id = self.get_argument("house_id")
        files = self.request.files.get("house_image")
        if not files:
            return self.write({"errcode": RET.PARAMERR, "errmsg": "请选择图片"})
        # 上传图片到七牛
        house_image = files[0]['body']
        image_name = storage(house_image)
        # print(image_name)
        if not image_name:
            return self.write({"errcode": RET.THIRDERR, "errmsg": "qiniu error"})

        try:
            #1、保存图片到数据库,并且设置房屋的主图片
            sql = "insert into ih_house_image(hi_house_id,hi_url) values(%s,%s);"
            self.db.cursor().execute(sql, (house_id, image_name))
            sql ="update ih_house_info set hi_index_image_url=%s " \
                  "where hi_house_id=%s and hi_index_image_url is null;"
            self.db.cursor().execute(sql, (image_name, house_id))
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "upload failed"})

        img_url = iamage_base_url + image_name
        # print(img_url)
        self.write({"errcode": RET.OK, "errmsg": "OK", "url": img_url})

class HouseListHandler(BaseHandler):
    '''
    房源列表信息
    '''
    def get(self, *args, **kwargs):
        """
        传入参数说明
        start_date 用户查询的起始时间 sd     非必传   ""          "2017-02-28"
        end_date    用户查询的终止时间 ed    非必传   ""
        area_id     用户查询的区域条件   aid 非必传   ""
        sort_key    排序的关键词     sk     非必传   "new"      "new" "booking" "price-inc"  "price-des"
        page        返回的数据页数     p     非必传   1
        """
        #获取参数
        start_date = self.get_argument('sd', '')
        end_date = self.get_argument('ed', '')
        area_id = self.get_argument('aid', '')
        sort_key = self.get_argument('sk', 'new')
        page = self.get_argument('p', '1')

        logging.debug(start_date)
        logging.debug(end_date)
        logging.debug(area_id)
        logging.debug(sort_key)
        logging.debug(page)

        #从redis取列表数据
        try:
            redis_key = "houses_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            house_info = self.redis.hget(redis_key, page)
            if house_info:
                # house_info = json.loads(house_info.decode())
                house_info = house_info.decode()
        except Exception as e:
            logging.error(e)
            house_info = None
        if house_info:
            logging.info("from redis")
            print(type(house_info))
            print(house_info)
            return self.write(house_info)

        # 数据查询
        # 涉及到表： ih_house_info 房屋的基本信息  ih_user_profile 房东的用户信息 ih_order_info 房屋订单数据

        sql = "select distinct hi_title as title,hi_house_id as house_id,hi_price as price,hi_room_count as room_count," \
              "hi_address as address,hi_order_count as order_count,up_avatar as avatar,hi_index_image_url as image_url, date_format(hi_ctime,'%%Y-%%m-%%d %%H:%%i:%%S') as hi_ctime" \
              " from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info" \
              " on hi_house_id=oi_house_id"

        sql_total_count = "select count(distinct hi_house_id) count from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id " \
                          "left join ih_order_info on hi_house_id=oi_house_id"

        sql_where = []  # 用来保存sql语句的where条件
        sql_params = {}  # 用来保存sql查询所需的动态数据

        if start_date and end_date:
            sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) " \
                       "or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
        elif end_date:
            sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["end_date"] = end_date
        if area_id:
            sql_part = "hi_area_id=%(area_id)s"
            sql_where.append(sql_part)
            sql_params["area_id"] = area_id

        if sql_where:
            sql += " where "
            sql += " and ".join(sql_where)
        # print(sql)
        # print(sql_params)
        # print(sql_where)
        # print(sql_total_count)
        # 有了where条件，先查询总条目数
        try:
            cur = self.db.cursor()
            cur.execute(sql_total_count)
            ret = cur.fetchall()[0]
        except Exception as e:
            logging.error(e)
            total_page = -1
        finally:
            cur.close()

        total_page = int(math.ceil(ret["count"] / float(HOUSE_LIST_PAGE_CAPACITY)))
        page = int(page)
        if page>total_page:
            return self.write(dict(errcode=RET.OK, errmsg="OK", data=[], total_page=total_page))

        # 排序
        if "new" == sort_key:  # 按最新上传时间排序
            sql += " order by hi_ctime desc"
        elif "booking" == sort_key:  # 最受欢迎
            sql += " order by hi_order_count desc"
        elif "price-inc" == sort_key:  # 价格由低到高
            sql += " order by hi_price asc"
        elif "price-des" == sort_key:  # 价格由高到低
            sql += " order by hi_price desc"

        # 分页
        # limit 10 返回前10条
        # limit 20,3 从20条开始，返回3条数据
        if 1 == page:
            sql += " limit %s" % (HOUSE_LIST_PAGE_CAPACITY * HOUSE_LIST_PAGE_CACHE_NUM)
        else:
            sql += " limit %s,%s" % ((page - 1) * HOUSE_LIST_PAGE_CAPACITY, HOUSE_LIST_PAGE_CAPACITY * HOUSE_LIST_PAGE_CACHE_NUM)
        logging.debug(sql)
        try:
            cur = self.db.cursor()
            cur.execute(sql, sql_params)
            data = cur.fetchall()
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
        finally:
            cur.close()
        for l in data:
            l['avatar'] = iamage_base_url + l['avatar'] if l.get("avatar") else ""
            l['image_url'] = iamage_base_url + l['image_url'] if l.get("image_url") else ""

        # 对与返回的多页面数据进行分页处理
        # 首先取出用户想要获取的page页的数据
        current_page_data = data[:HOUSE_LIST_PAGE_CAPACITY]
        house_data = {}
        house_data[page] = json.dumps(dict(errcode=RET.OK, errmsg="OK", data=current_page_data, total_page=total_page))
        # 将多取出来的数据分页
        i = 1
        while 1:
            page_data = data[i * HOUSE_LIST_PAGE_CAPACITY: (i + 1) * HOUSE_LIST_PAGE_CAPACITY]
            if not page_data:
                break
            house_data[page + i] = json.dumps(dict(errcode=RET.OK, errmsg="OK", data=page_data, total_page=total_page))
            i += 1
        try:
            redis_key = "houses_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            self.redis.hmset(redis_key, house_data)
            self.redis.expire(redis_key, REDIS_HOUSE_LIST_EXPIRES_SECONDS)
        except Exception as e:
            logging.error(e)
        # print(type(house_data[page]))
        # print(house_data[page])
        self.write(house_data[page])


















