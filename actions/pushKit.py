import requests


# 消息通知聚合类
class pushKit:
    # 初始化类
    def __init__(self, option):
        self.option = option
        self.type = option['method']

    def sendMsg(self, title, msg, user=''):
        if 'notifyOption' not in user:
            return '该用户未配置推送,已取消发送！'
        if 'rcvAcc' not in user['notifyOption']:
            return '该用户未配置推送,已取消发送！'
        if user['notifyOption']['rcvAcc'] == "":
            return '该用户未配置推送,已取消发送！'

        userOption = user['notifyOption']
        # 获取接收账号
        rcvAcc = userOption['rcvAcc']
        # 获取全局推送模式
        method = self.type
        # 获取用户指定的推送模式
        if 'method' in userOption:
            method = userOption['method']

        # 判断推送类型
        if method == 0:
            return '消息推送服务未启用'
        if method == 1:
            return self.sendMsgByQyWx(rcvAcc, title, msg)
        if method == 2:
            return self.sendMsgByServerChan(rcvAcc, title, msg)

        return '推送参数配置错误,已取消发送！'

    # 企业微信应用推送
    def sendMsgByQyWx(self, rcvAcc, title, message):
        wxConfig = self.option['qywxOption']

        def get_access_token(wxConfig):
            get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
            response = requests.get(get_token_url, params=wxConfig).json()
            if response.get('access_token'):
                return response['access_token']
            else:
                print(response)
                return '获取access_token失败,已取消企业微信推送'

        if wxConfig['corpid'] and wxConfig['corpsecret']:
            try:
                access_token = get_access_token(wxConfig)
                if isinstance(access_token, str):
                    params = {
                        'touser': rcvAcc,
                        "agentid": wxConfig['agentid'],
                        "msgtype": "text",
                        'text': {
                            'content': f'{title}\n{message}'
                        }
                    }
                    url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
                    response = requests.post(url=url, json=params).json()
                    # print(response)
                    return '企业微信推送成功' if response[
                                             'errmsg'] == 'ok' else response
                else:
                    print(access_token)
                    return access_token
            except Exception as e:
                return '企业微信推送失败,%s' % (e)
        else:
            return '企业微信应用配置错误,请检查qywxOption'

    # Server酱推送
    def sendMsgByServerChan(self, key, title, msg):
        if self.option['serverChanOption']['baseUrl'] == '':
            return 'Server酱的baseUrl为空,设置baseUrl后才能发送邮件'
        url = '{}{}.send'.format(
            self.option['serverChanOption']['baseUrl'], key)
        params = {'title': title, 'desp': msg}
        res = requests.post(url, params=params).json()
        if res['code'] == 0:
            return 'Server酱推送成功'
        else:
            return 'Server酱推送失败,' + res['message']
