# -*- coding: utf-8 -*-
# @Author  :songtao
# @File    :image_storage.py

from qiniu import Auth, put_data
import qiniu.config

#需要填写你的 Access Key 和 Secret Key
access_key = 's-5_NpYiAMNzVgNYWZ7byUsyG100Ss4mL1M3-hLN'
secret_key = 'gppG6C31qPFmmOnVtQQw9rPGeLMt2dFUXTTNMZmw'

def storage(image_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome'

    # 上传到七牛后保存的文件名
    # key = 'my-python-logo.png';

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'

    ret, info = put_data(token, None, image_data)
    # print(info)
    # assert ret['key'] == key
    # assert ret['hash'] == etag(localfile)
    return ret['key']

if __name__=='__main__':
    file_name = input("输入用户名：")
    file = open(file_name, "rb")
    file_data = file.read()
    key = storage(file_data)
    # print(key)
    file.close()


