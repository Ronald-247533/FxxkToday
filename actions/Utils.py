import base64
import json
import random
import rsa
import sys
import yaml
from io import BytesIO
from Crypto.Cipher import AES
from datetime import datetime, timedelta, timezone
import os
from pyDes import des, CBC, PAD_PKCS5
import re
import uuid
import hashlib
import urllib.parse


class Utils:
    def __init__(self):
        pass

    # 获取指定长度的随机字符
    @staticmethod
    def randString(length):
        baseString = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
        data = ''
        for i in range(length):
            data += baseString[random.randint(0, len(baseString) - 1)]
        return data

    @staticmethod
    def getYmlConfig(yaml_file=os.path.join(os.path.dirname(__file__),
                                            '../config.yml')):
        file = open(yaml_file, 'r', encoding="utf-8")
        file_data = file.read()
        file.close()
        config = yaml.load(file_data, Loader=yaml.FullLoader)
        return dict(config)

    # aes加密的实现
    @staticmethod
    def encryptAES(data, key):
        ivStr = '\x01\x02\x03\x04\x05\x06\x07\x08\x09\x01\x02\x03\x04\x05\x06\x07'
        aes = AES.new(bytes(key, encoding='utf-8'), AES.MODE_CBC,
                      bytes(ivStr, encoding="utf8"))
        text_length = len(data)
        amount_to_pad = AES.block_size - (text_length % AES.block_size)
        if amount_to_pad == 0:
            amount_to_pad = AES.block_size
        pad = chr(amount_to_pad)
        data = data + pad * amount_to_pad
        text = aes.encrypt(bytes(data, encoding='utf-8'))
        text = base64.encodebytes(text)
        text = text.decode('utf-8').strip()
        return text

    @staticmethod
    def encryptRSA(message, m, e):
        mm = int(m, 16)
        ee = int(e, 16)
        rsa_pubkey = rsa.PublicKey(mm, ee)
        crypto = Utils._encrypt_rsa(message.encode(), rsa_pubkey)
        return crypto.hex()

    @staticmethod
    def _pad_for_encryption_rsa(message, target_length):
        message = message[::-1]
        max_msglength = target_length - 11
        msglength = len(message)
        padding = b''
        padding_length = target_length - msglength - 3
        for i in range(padding_length):
            padding += b'\x00'
        return b''.join([b'\x00\x00', padding, b'\x00', message])

    @staticmethod
    def _encrypt_rsa(message, pub_key):
        keylength = rsa.common.byte_size(pub_key.n)
        padded = Utils._pad_for_encryption_rsa(message, keylength)
        payload = rsa.transform.bytes2int(padded)
        encrypted = rsa.core.encrypt_int(payload, pub_key.e, pub_key.n)
        block = rsa.transform.int2bytes(encrypted, keylength)
        return block

    @staticmethod
    def log(content):
        print(Utils.getTimeStr() + " V%s %s" %
              (Utils.getYmlConfig()['Version'], content))
        sys.stdout.flush()

    @staticmethod
    def getTimeStr():
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 利用hook判断当前返回的状态码是否正常
    @staticmethod
    def checkStatus(request, *args, **kwargs):
        if request.status_code == 418:
            raise Exception('418错误,当前IP地址已被今日校园封禁')

    @staticmethod
    def DESEncrypt(s, key='XCE927=='):
        key = key
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(s)
        return base64.b64encode(encrypt_str).decode()

    @staticmethod
    def md5(str):
        md5 = hashlib.md5()
        md5.update(str.encode("utf8"))
        return md5.hexdigest()

    @staticmethod
    def submitFormData(env):
        extension = {
            "lon": env.userInfo['lon'],
            "model": "MI 6",
            "appVersion": "9.0.14",
            "systemVersion": "8.0.0",
            "userId": env.userInfo['username'],
            "systemName": "android",
            "lat": env.userInfo['lat'],
            "deviceId": str(uuid.uuid1())
        }
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Linux; Android 8.0.0; MI 6 Build/OPR1.170623.027; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 okhttp/3.12.4 cpdaily/9.0.14 wisedu/9.0.14',
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': Utils.DESEncrypt(json.dumps(extension)),
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Encoding': 'gzip',
            'Host': re.findall('//(.*?)/', env.host)[0],
            'Connection': 'Keep-Alive'
        }
        Utils.log('正在加密表单数据')
        bodyString = Utils.encryptAES(
            json.dumps(env.submitData), 'SASEoK4Pa5d4SssO')
        env.submitData['bodyString'] = bodyString
        # print(env.submitData)
        formData = {
            'version':
                'first_v3',
            'calVersion':
                'firstv',
            'bodyString': bodyString,
            'sign': Utils.md5(urllib.parse.urlencode(env.submitData) + "&SASEoK4Pa5d4SssO")
        }
        formData.update(extension)
        Utils.log('正在尝试提交数据')
        return env.session.post(env.host + env.submitApi,
                                headers=headers,
                                data=json.dumps(formData),
                                verify=False)

    @staticmethod
    def getApis(type):
        apis = [
            [
                'wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList',
                'wec-counselor-collector-apps/stu/collector/detailCollector',
                'wec-counselor-collector-apps/stu/collector/getFormFields',
                'wec-counselor-collector-apps/stu/collector/submitForm',
                'wec-counselor-collector-apps/stu/obs/getUploadPolicy',
                'wec-counselor-collector-apps/stu/collector/previewAttachment'
            ],
            [
                'wec-counselor-sign-apps/stu/sign/getStuSignInfosInOneDay',
                'wec-counselor-sign-apps/stu/sign/detailSignInstance',
                'wec-counselor-sign-apps/stu/sign/submitSign',
                'wec-counselor-sign-apps/stu/obs/getUploadPolicy',
                'wec-counselor-sign-apps/stu/sign/previewAttachment'
            ],
        ]
        return apis[type]
