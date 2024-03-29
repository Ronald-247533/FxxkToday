from actions.wiseLoginService import wiseLoginService
from actions.collection import Collection
from actions.pushKit import pushKit
from actions.Utils import Utils
from time import sleep
import random


def main():
    Utils.log("自动化任务开始执行")
    config = Utils.getYmlConfig()
    push = pushKit(config['notifyOption'])
    httpProxy = config['httpProxy'] if 'httpProxy' in config else ''
    for user in config['users']:
        times = random.randint(0, 9)
        Utils.log(
            f"{times}s后开始执行用户{user['user']['username'] if user['user']['username'] else '默认用户'}的任务"
        )
        sleep(times)
        if config['debug']:
            msg = working(user, httpProxy)
        else:
            try:
                msg = working(user, httpProxy)
                ret = True
            except Exception as e:
                msg = str(e)
                ret = False
            ntm = Utils.getTimeStr()
            if ret == True:
                # 此处需要注意就算提示成功也不一定是真的成功，以实际为准
                Utils.log(msg)
                if 'SUCCESS' in msg:
                    msg = push.sendMsg(
                        '签到成功通知',
                        '%s，服务器(V%s)于%s尝试签到成功!' % (
                            user['user']['username'], config['Version'], ntm),
                        user['user'])
                else:
                    msg = push.sendMsg(
                        '签到异常通知', '%s，服务器(V%s)于%s尝试签到异常!\n异常信息:%s' %
                        (user['user']['username'], config['Version'], ntm, msg), user['user'])
            else:
                Utils.log("Error:" + msg)
                msg = push.sendMsg(
                    '签到失败通知', '%s，服务器(V%s)于%s尝试签到失败!\n错误信息:%s' %
                    (user['user']['username'], config['Version'], ntm, msg), user['user'])
            Utils.log(msg)
    Utils.log("自动化任务执行完毕")


def working(user, httpProxy):
    Utils.log('正在获取登录地址')
    wise = wiseLoginService(user['user'], httpProxy)
    Utils.log('开始尝试登录账号')
    wise.login()
    sleep(1)
    # 登陆成功
    # 信息收集的代码
    Utils.log('开始执行收集任务')
    collection = Collection(wise, user['user'])
    collection.queryForm()
    collection.fillForm()
    sleep(1)
    msg = collection.submitForm()
    return msg


if __name__ == '__main__':
    main()
