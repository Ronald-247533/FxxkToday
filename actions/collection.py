import json
from actions.Utils import Utils
from actions.wiseLoginService import wiseLoginService


class Collection:
    # 初始化信息收集类
    def __init__(self, wiseLoginService: wiseLoginService, userInfo):
        self.session = wiseLoginService.session
        self.host = wiseLoginService.campus_host
        self.userInfo = userInfo
        self.form = None
        self.collectWid = None
        self.formWid = None
        self.schoolTaskWid = None
        self.instanceWid = None
        self.historyTaskData = None
        self.apis = Utils.getApis(0)

    # 查询表单
    def queryForm(self):
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        queryUrl = self.host + self.apis[0]
        params = {"pageSize": 20, "pageNumber": 1}
        res = self.session.post(queryUrl,
                                data=json.dumps(params),
                                headers=headers,
                                verify=False).json()
        if len(res['datas']['rows']) < 1:
            raise Exception('当前暂时没有未完成的信息收集哦！')
        for item in res['datas']['rows']:
            if item['isHandled'] == 0:
                self.collectWid = item['wid']
                self.formWid = item['formWid']
                self.instanceWid = item['instanceWid']
        if (self.formWid == None):
            raise Exception('当前暂时没有未完成的信息收集哦！')
        detailUrl = self.host + self.apis[1]
        res = self.session.post(detailUrl,
                                headers=headers,
                                data=json.dumps({
                                    "collectorWid": self.collectWid,
                                    "instanceWid": self.instanceWid
                                }),
                                verify=False).json()
        self.schoolTaskWid = res['datas']['collector']['schoolTaskWid']
        getFormUrl = self.host + self.apis[2]
        params = {
            "pageSize": 100,
            "pageNumber": 1,
            "formWid": self.formWid,
            "collectorWid": self.collectWid,
            "instanceWid": self.instanceWid
        }
        res = self.session.post(getFormUrl,
                                headers=headers,
                                data=json.dumps(params),
                                verify=False).json()
        self.form = res['datas']['rows']

    # 获取历史签到任务详情
    def getHistoryTaskInfo(self):
        '''获取历史签到任务详情'''
        headers = self.session.headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        # 获取首页信息, 获取页数
        pageSize = 20
        url = f'{self.host}wec-counselor-collector-apps/stu/collector/queryCollectorHistoryList'
        pageReq = {"pageNumber": 1, "pageSize": pageSize}
        pageNumber = 0
        totalSize = 1
        # 按页遍历
        while pageNumber*pageSize <= totalSize:
            pageNumber += 1
            pageReq["pageNumber"] = pageNumber
            # 获取**任务列表**数据
            res = self.session.post(url, headers=headers,
                                    data=json.dumps(pageReq), verify=False)
            res = res.json()
            Utils.log(f"获取到第{pageNumber}页历史信息收集数据")
            # 在**首页**获取历史信息收集**总数**
            if pageNumber == 1:
                # 历史信息收集总数
                totalSize = res['datas']['totalSize']
                # 如果没有获取到历史任务则报错
                if totalSize < 0:
                    raise Exception(f"没有获取到历史任务")
            # 按页中任务遍历
            for task in res['datas']['rows']:
                if task['isHandled'] == 1 and task['formWid'] == self.formWid:
                    # 找到和当前任务匹配的历史已处理任务，开始获取表单
                    historyInstanceWid = task['instanceWid']
                    historyWid = task['wid']
                    # 模拟请求
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/getUnSeenQuestion'
                    self.session.post(url, headers=headers, data=json.dumps(
                        {"wid": self.collectWid, "instanceWid": self.instanceWid}), verify=False)
                    # 模拟请求:获取历史信息收集信息
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/detailCollector'
                    self.session.post(url, headers=headers, data=json.dumps(
                        {"collectorWid": self.collectWid, "instanceWid": self.instanceWid}), verify=False)
                    # 获取表单
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/getFormFields'
                    formReq = {"pageNumber": 1, "pageSize": 9999, "formWid": self.formWid,
                               "collectorWid": historyWid, "instanceWid": historyInstanceWid}
                    res = self.session.post(url, headers=headers, data=json.dumps(formReq),
                                            verify=False)
                    res = res.json()
                    # 模拟请求
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/queryNotice'
                    self.session.post(url, headers=headers,
                                      data=json.dumps({}), verify=False)
                    # 处理表单
                    form = res['datas']['rows']
                    # 逐个处理表单内问题
                    for item in form:
                        # 填充额外参数
                        item['show'] = True
                        item['formType'] = '0'  # 盲猜是任务类型、待确认
                        item['sortNum'] = str(item['sort'])  # 盲猜是sort排序
                        if item['fieldType'] == '2':
                            '''如果是单选题，需要删掉多余选项'''
                            item['fieldItems'] = list(
                                filter(lambda x: x['isSelected'], item['fieldItems']))
                            if item['fieldItems']:
                                '''如果已选有选项，则将itemWid填入value中'''
                                item['value'] = item['fieldItems'][0]['itemWid']
                        elif item['fieldType'] == '3':
                            '''如果是多选题，也需要删掉多余选项'''
                            item['fieldItems'] = list(
                                filter(lambda x: x['isSelected'], item['fieldItems']))
                            if item['fieldItems']:
                                '''如果已选有选项，则将itemWid填入value中'''
                                item['value'] = ','.join(
                                    [i['itemWid'] for i in item['fieldItems']])
                    self.historyTaskData = form
                    return self.historyTaskData
        # 如果没有获取到历史信息收集则报错
        raise Exception(f"没有找到匹配的历史任务", 301)

    # 填写表单

    def fillForm(self):
        if self.userInfo['getHistorySign'] == 1:
            self.getHistoryTaskInfo()
            self.form = self.historyTaskData
        else:
            index = 0
            onlyRequired = self.userInfo['onlyRequired'] if 'onlyRequired' in self.userInfo else 1
            for formItem in self.form[:]:
                if onlyRequired == 1:
                    if not formItem['isRequired']:
                        # 移除非必填选项
                        self.form.remove(formItem)
                        continue
                try:
                    userForm = self.userInfo['forms'][index]['form']
                except:
                    raise Exception('请检查forms配置是否正确！')
                # 忽略用户指定题目
                if 'ignore' in userForm and userForm['ignore'] == 1:
                    formItem['value'] = None
                    # 设置显示为false
                    formItem['show'] = False
                    # 清空所有的选项
                    if 'fieldItems' in formItem:
                        formItem['fieldItems'].clear()
                    index += 1
                    continue
                # 判断用户是否需要检查标题
                if self.userInfo['checkTitle'] == 1:
                    # 如果检查到标题不相等
                    if formItem['title'] != userForm['title']:
                        raise Exception(
                            f'\r\n第{index + 1}个配置项的标题不正确\r\n您的标题为：[{userForm["title"]}]\r\n系统的标题为：[{formItem["title"]}]'
                        )
                formType = formItem['fieldType']
                if 'forceType' in userForm and userForm['forceType']:
                    formType = userForm['forceType']
                # 文本选项直接赋值
                if formType in ('1', '5', '6', '7', '11', '12'):
                    formItem['value'] = userForm['value']
                # 单选框填充
                elif formType == '2':
                    # 单选需要移除多余的选项
                    fieldItems = formItem['fieldItems']
                    for fieldItem in fieldItems[:]:
                        if fieldItem['content'] == userForm['value']:
                            formItem['value'] = fieldItem['itemWid']
                            if fieldItem['isOtherItems'] and fieldItem[
                                    'otherItemType'] == '1':
                                if 'extra' not in userForm:
                                    raise Exception(
                                        f'\r\n第{index + 1}个配置项的选项不正确,该选项需要extra字段')
                                fieldItem['contentExtend'] = userForm['extra']
                        else:
                            fieldItems.remove(fieldItem)
                    if len(fieldItems) != 1:
                        raise Exception(f'\r\n第{index + 1}个配置项的选项不正确,该选项为必填单选')
                # 多选填充
                elif formType == '3':
                    fieldItems = formItem['fieldItems']
                    userItems = userForm['value'].split('|')
                    tempValue = []
                    for fieldItem in fieldItems[:]:
                        if fieldItem['content'] in userItems:
                            tempValue.append(fieldItem['itemWid'])
                            if fieldItem['isOtherItems'] and fieldItem[
                                    'otherItemType'] == '1':
                                if 'extra' not in userForm:
                                    raise Exception(
                                        f'\r\n第{index + 1}个配置项的选项不正确,该选项需要extra字段')
                                fieldItem['contentExtend'] = userForm['extra']
                        else:
                            fieldItems.remove(fieldItem)
                    if len(fieldItems) == 0:
                        raise Exception(f'\r\n第{index + 1}个配置项的选项不正确,该选项为必填多选')
                    formItem['value'] = ','.join(tempValue)
                else:
                    raise Exception(
                        f'\r\n第{index + 1}个配置项的类型{formItem.fieldType}未适配')
                index += 1

    # 提交表单
    def submitForm(self):
        self.submitData = {
            "formWid": self.formWid,
            "address": self.userInfo['address'],
            "collectWid": self.collectWid,
            "instanceWid": self.instanceWid,
            "schoolTaskWid": self.schoolTaskWid,
            "form": self.form,
            "uaIsCpadaily": True,
            "latitude": self.userInfo['lat'],
            'longitude': self.userInfo['lon']
        }
        self.submitApi = self.apis[3]
        res = Utils.submitFormData(self).json()
        return res['message']
