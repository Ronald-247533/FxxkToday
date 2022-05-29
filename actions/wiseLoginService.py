import re
import requests
from urllib3.exceptions import InsecureRequestWarning
from actions.casLogin import casLogin
from actions.Utils import Utils

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class wiseLoginService:
    # 初始化本地登录类
    def __init__(self, userInfo, httpProxy):
        if None == userInfo['username'] or '' == userInfo[
            'username'] or None == userInfo['password'] or '' == userInfo[
            'password']:
            raise Exception('初始化类失败，请键入完整的参数（用户名，密码，学校名称）')
        self.username = userInfo['username']
        self.password = userInfo['password']
        self.session = requests.session()
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Linux; Android 8.0.0; MI 6 Build/OPR1.170623.027; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 okhttp/3.12.4',
        }
        self.session.headers = headers
        self.session.hooks['response'].append(Utils.checkStatus)
        self.session.adapters.DEFAULT_RETRIES = 5
        if httpProxy != '':
            Utils.log('全局代理已启用')
            self.session.proxies = {'http': httpProxy, 'https': httpProxy}
        self.session.hooks['response'].append(Utils.checkStatus)
        self.login_url = ''
        self.campus_host = ''
        self.login_host = ''
        self.loginEntity = None
        self.login_type = ''

    # 借助api获取学校的登陆url
    def getLoginUrl(self):
        params = {'ids': 'hlju'}
        data = self.session.get(
            'https://mobile.campushoy.com/v6/config/guest/tenant/info',
            params=params,
            verify=False,
        ).json()['data'][0]
        joinType = data['joinType']
        ampUrl = data['ampUrl']
        ampUrl2 = data['ampUrl2']
        if 'campusphere' in ampUrl:
            clientUrl = ampUrl
        elif 'campusphere' in ampUrl2:
            clientUrl = ampUrl2
        else:
            raise Exception('未找到客户端登录地址')
        res = self.session.get(clientUrl, verify=False)
        self.campus_host = re.findall('\w{4,5}\:\/\/.*?\/',
                                      clientUrl)[0]
        self.login_url = res.url
        self.login_host = re.findall('\w{4,5}\:\/\/.*?\/', res.url)[0]
        self.login_type = joinType

    # 本地化登陆
    def login(self):
        # 获取学校登陆地址
        self.getLoginUrl()

        self.loginEntity = casLogin(self.username, self.password,
                                    self.login_url, self.login_host,
                                    self.session)
        self.session.cookies = self.loginEntity.login()
