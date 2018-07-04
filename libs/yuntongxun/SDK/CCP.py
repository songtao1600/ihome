# coding:utf-8
# from . import CCPRestSDK

from libs.yuntongxun.SDK.CCPRestSDK import REST

_accountSid = '8a216da863f8e6c2016434703a231f2b'
_accountToken = 'a69cbc83987c461897871620ed975246'
_appId = '8a216da863f8e6c2016434703a811f32'
_serverIP='sandboxapp.cloopen.com'
_serverPort=8883
_softVersion='2013-12-26'

class _CPP(object):
    def __init__(self):
        self.rest = REST(_serverIP, _serverPort, _softVersion)
        self.rest.setAccount(_accountSid, _accountToken)
        self.rest.setAppId(_appId)

    @classmethod
    def instance(cls):
        if not hasattr(cls,"_instance"):
            cls._instance = cls()
        return cls._instance


    def sendTemplateSMS(self, to, datas, tempId):
        # time.sleep(15)
        result = self.rest.sendTemplateSMS(to, datas, tempId)
        # result = {}
        # result['statusCode'] = '000000'
        return result

cpp = _CPP.instance()

# if __name__=='__main__':
#     cpp.sendTemplateSMS('13001006207', ['1234', 5], 1)