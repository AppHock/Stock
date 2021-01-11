import tushare as tu
import time
import datetime
import numpy as np
import sys, os
import codecs
import csv
from threading import Thread

import mmap
import contextlib
import time
import base64
import json
import pandas as pd

g_currentDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(g_currentDir + '/../../../')

# token = 'ed854a25065df86d7d0dddf9161abc26e7eff21ccd2ba4d0d3d3e28c' # 大鹏的token
token = '47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899' # 阿文的token

tu.set_token(token)
pro = tu.pro_api()

# 逻辑：获得所有股票代码
def getAllStokeCode():
    stokeCodes = []
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code')
    # data = pro.stock_basic(exchange='', list_status='L', fields='ts_code, symbol, name, area, industry, list_date')
    # codeString = ((codeString + "," + code) if len(codeString)>0 else code)

    for i in range(0, data.size):
        code = data.values[i][0]
        stokeCodes.append(code)
    return stokeCodes

# 逻辑：获得所有股票名称,代码,行业信息
def getAllStokeInfo():
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code, name, industry')
    saveDir = os.getcwd() + '/StokeInfo'
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    path = saveDir + '/行业信息' + '.csv'
    symbolFile = open(path, 'w+', encoding='utf8')
    symbolFile.write('代码,名称,行业\n')
    symbolFile.flush()

    for codeInfo in data.values:
        code = codeInfo[0]
        name = codeInfo[1]
        industry = codeInfo[2]

        s = '%s,%s,%s\n' % (code, name, industry)
        symbolFile.write(s)
        symbolFile.flush()
    print('所有股票基本信息更新完成')

# 读取本地所有股票信息
def getCodeInfo():
    saveDir = os.getcwd() + '/StokeInfo/'
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    path = saveDir + "行业信息.csv"
    industyWithCode = {}
    with codecs.open(path, 'r', encoding='utf8') as fp:
        fp_key = csv.reader(fp)
        
        for csv_key in fp_key:
            csv_reader = csv.DictReader(fp, fieldnames=csv_key)
            for row in csv_reader:
                codeInfo = {}
                code = row['代码']
                codeInfo['code'] = row['代码']
                codeInfo['industy'] = row['行业']
                codeInfo['name'] = row['名称']
                industyWithCode[code] = codeInfo
    return industyWithCode

# 获得前一天的时间
def getPreDateAndUnixTime(dateUnixTime):
    currentUnixTime = dateUnixTime - 60 * 60 * 24 * 1
    return [unixTime2LocalDate(currentUnixTime, "%Y%m%d"), currentUnixTime]

def getCurrentDayDate():
    timeStr = time.strftime("%H", time.localtime(time.time()))
    if int(timeStr) >= 16:
        return time.strftime("%Y%m%d", time.localtime(time.time()))
    else:
        currentTime = getCurrentUnixTime()
        return getPreDateAndUnixTime(currentTime)[0]

def getCurrentUnixTime():
    return int(time.mktime(datetime.datetime.now().timetuple()))

# date字符串转Unix时间
def date2UnixTime(dt, dateFormat="%Y-%m-%d %H:%M:%S"):
    #转换成时间数组 %Y-%m-%d %H:%M:%S
    timeArray = time.strptime(dt, dateFormat)
    #转换成时间戳
    timestamp = time.mktime(timeArray)
    return timestamp

# Unix时间转date字符串
def unixTime2LocalDate(timestamp, dateFormat="%Y-%m-%d %H:%M:%S"):
    #转换成localtime
    time_local = time.localtime(timestamp)
    #转换成新的时间格式(2016-05-05 20:28:54)
    dt = time.strftime(dateFormat, time_local)
    return dt

# 逻辑：从本地获取数据
def getLocalData():
    localData = {}
    saveDir = os.getcwd() + '/DayKLine/'
    if os.path.exists(saveDir):
        a = os.listdir(saveDir)
        
        for j in a:
            csv_storage = []
            saveDir = os.getcwd() + '/DayKLine/'
            path = saveDir+j
            # 剔除隐藏文件
            if j.startswith('.'):
                continue
            with codecs.open(path, 'r', encoding='utf8') as fp:
                fp_key = csv.reader(fp)
                
                for csv_key in fp_key:
                    csv_reader = csv.DictReader(fp, fieldnames=csv_key)
                    for row in csv_reader:
                        csv_dict = dict(row)
                        csv_storage.append(csv_dict)
            localData[j] = csv_storage

    data = bytes('{}'.format(localData), 'utf8')
    shareData(data)

# 逻辑：将本地读取的数据缓存在临时内存中
def shareData(data):
    with open("test.dat", "w") as f:
        f.write('\x00' * len(data))
 
    with open('test.dat', 'r+') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)) as m:
            m.write(data)
            m.flush()
            print('本地数据服务，已开启')
            # 通过while循环保证数据一直保存在内存中
            # while True:
            #     time.sleep(2)

# 逻辑：获取最近dayNum天的所有股票的数据
def getAllStokeData(dayNum):
    saveDir = os.getcwd() + '/DayKLine/'
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    allStokeDate = getRecentData(dayNum)
    allCodes = list(allStokeDate.keys())

    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        path = saveDir + code + '.csv'
        symbolFile = open(path, 'w+', encoding='utf8')
        symbolFile.write('ts_code, trade_date, open, high, low, close, pct_chg, vol\n')
        symbolFile.flush()
        for data in dataArr:
            s = '%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
                    code,
                    data['trade_date'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['pct_chg'],
                    data['vol'],
                )
            symbolFile.write(s)
            symbolFile.flush()
    print('%d天交易数据下载完成' % dayNum)
    return allStokeDate

# 逻辑：获取最新几天的数据， time默认为0，time主要解决因停市导致数据没有的问题
def getRecentData(dayNum, time=0):
    currentTime = getCurrentUnixTime()
    dateAndUnix = getPreDateAndUnixTime(currentTime)
    date = dateAndUnix[0]
    dateUnix = dateAndUnix[1]

    if 1: #如果当天下午4点以后，则可以获得到当前数据
        date = unixTime2LocalDate(currentTime, "%Y%m%d")
        dateUnix = currentTime

    allStokeDate = {}
    # for循环获取每天的全部股票的交易信息
    tempTime = 0
    
    if dayNum == time == 0:
        print("输入的日期格式不对，dayNum和time不能同时为0")
    readDay = 0
    if dayNum:
        readDay = dayNum
    else:
        readDay = time
    for i in range(readDay):
        while 1:
            if time & (tempTime == time):
                return allStokeDate
            if time:
                tempTime += 1
                if tempTime > time:
                    return allStokeDate
            # 获取日线行情  ------ https://www.waditu.com/document/2?doc_id=27
            # vol:成交量、pct_chg:涨跌幅
            data = pro.daily(trade_date=date, fields='ts_code, trade_date, open, high, low, close, pct_chg, vol')
            dateAndUnix = getPreDateAndUnixTime(dateUnix)
            date = dateAndUnix[0]
            dateUnix = dateAndUnix[1]
            if len(data.values) != 0:
                for stokeData in data.values:
                    code = stokeData[0]
                    dataArr = allStokeDate.get(code, [])
                    dic = {}
                    index = 1
                    dic['trade_date'] = stokeData[1]
                    dic['open'] = stokeData[index+1]
                    dic['high'] = stokeData[index+2]
                    dic['low'] = stokeData[index+3]
                    dic['close'] = stokeData[index+4]
                    dic['pct_chg'] = stokeData[index+5]
                    dic['vol'] = stokeData[index+6]
                    
                    # 时间越小，在数组位置约靠后
                    dataArr.append(dic)
                    allStokeDate[code] = dataArr
                break
    return allStokeDate

# 逻辑：新增新的数据
def addNewData():
    # 获取本地保存的最新的日期(20200703)、时间戳
    reTopDate = getReTopDate()
    reTopUnix = date2UnixTime(reTopDate, "%Y%m%d")
    # 获取当天Unix时间戳、当天日期
    currentTime = getCurrentUnixTime()

    # 计算出本地保存最新的日期到今天日期差几天
    unixTime = currentTime - reTopUnix
    if  unixTime % (24 * 60 * 60) == 0:
        dateNum = int(unixTime / (24 * 60 * 60))
    else:
        dateNum = int(unixTime / (24 * 60 * 60)) + 1
    print(dateNum-1)
    if dateNum-1 <= 0:
        return
    allStokeDate = getRecentData(0, dateNum-1)
    if len(list(allStokeDate.keys())) > 0:
        # 开始往本地csv文件头部插入新的数据
        writeNewDayData(allStokeDate)
        
# 逻辑：写入新的交易日K数据
def writeNewDayData(dict):
    # 获取本地所有数据
    allLocalData = getLocalKLineData(0)

    # 将当前目录下的所有文件名称读取进来
    saveDir = os.getcwd() + '/DayKLine/'
    fileNames = os.listdir(saveDir)
    for name in fileNames:
        # 每个csv文件全路径
        path = saveDir + name
        symbolFile = open(path, 'w+', encoding='utf8')
        code = name[0:9]
        if code not in dict.keys():
            continue
        dataArr = dict[code]
        allLocalArr = []
        if code in allLocalData.keys():
            allLocalArr = allLocalData[code]
        # 合并之后的最新的数据数组
        allArr = dataArr + allLocalArr

        # 写入头部名称
        symbolFile.write('ts_code, trade_date, open, high, low, close, pct_chg, vol\n')
        symbolFile.flush()
        # dataframe = pd.DataFrame({'a_name':a,'b_name':b})
        for data in allArr:
            s = '%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
                    code,
                    data['trade_date'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['pct_chg'],
                    data['vol'],
                )
            symbolFile.write(s)
            symbolFile.flush()
    print('保存完成')
        # 需要优化，只需要下载最新的几天保存
        #字典中的key值即为csv中列名
        # dataframe = pd.DataFrame({'a_name':'','b_name':''})

        #将DataFrame存储为csv,index表示是否显示行名，default=True
        # dataframe.to_csv(path, sep=',', model = 'a')

# 逻辑：获得本地保存的数据的最新日期
def getReTopDate():
    with open('/Users/chengpeng2/Desktop/choice/test.dat', 'r') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
            s = m.read(m.size())
            # 单引号转双引号
            bs = str(s, encoding = "utf8").replace('\'', '\"')
            # 去掉空格
            bs = bs.replace('\" ', '\"')
            dict = json.loads(bs)
            date = (list(dict.values())[1][0])['trade_date']
            return date

# 逻辑：获得本地最近dayNum天的交易日K线数据
def getLocalKLineData(dayNum):
    with open('/Users/chengpeng2/Desktop/choice/test.dat', 'r') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
            s = m.read(m.size())
            # 单引号转双引号
            bs = str(s, encoding = "utf8").replace('\'', '\"')
            # 去掉空格
            bs = bs.replace('\" ', '\"')
            dict = json.loads(bs)
            allStokeDate = {}
            allCodes = list(dict.keys())
            # 大涨，微涨跌[-0.5,1]，微涨跌[-0.5,1]，跌[-5,-2]
            for i in range(len(allCodes)):
                code = allCodes[i]
                dataArr = dict[code]
                toIndex = 0
                if dayNum == 0:
                    toIndex = len(dataArr)
                else:
                    toIndex = dayNum
                tempArr = dataArr[0:toIndex]
                for temp in tempArr:
                    for key in temp.keys():
                        if (key != 'ts_code') & (key != 'trade_date'):
                            temp[key] = float(temp[key])
                code = code.replace('.csv', '')
                allStokeDate[code] = tempArr
                
            return allStokeDate

# 逻辑：#查询当前所有正常上市交易的股票列表
def getCodeName():
    codeAndName = {}
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    for codeInfo in data.values:
        if len(codeInfo) >= 3:
            info = {}
            code = codeInfo[0]
            name = codeInfo[2]
            if '退' in name:
                continue
            info['name'] = name
            codeAndName[code] = info
    return codeAndName

# 逻辑：通过股票代码获取每日指标【公司名称，市盈率，总市值，流通市值。。。等】
def get_daily_basic(codesStr, date=getCurrentDayDate()):
    codeAndName = getCodeName()
    codeAllInfo = {}
    data = pro.daily_basic(ts_code=codesStr, trade_date=date, fields='ts_code,pe,total_mv,circ_mv')
    for codeInfo in data.values:
        if len(codeInfo) == 4:
            code = codeInfo[0]
            pe = codeInfo[1]
            total_mv = codeInfo[2]
            circ_mv = codeInfo[3]
            info = codeAndName.get(code)
            if not info:
                continue
            info['pe'] = pe
            info['total_mv'] = total_mv
            info['circ_mv'] = circ_mv
            codeAllInfo[code] = info
    return codeAllInfo

# 逻辑：获取前复权的250日均线
def getQFQVerPrice():
    # data = tu.pro_bar(ts_code='000001.SZ', adj='qfq', start_date='20180101', end_date='20180111')
    data = tu.pro_bar(ts_code='000001.SZ', start_date='20180101', end_date='20181011', adj='qfq')
    for codeInfo in data.values:
        print(codeInfo)

def getLowPriceMainMoney_3():
    #获取单日全部股票数据
    code_moneyflow = {}
    dataArr = ['20201119', '20201118', '20201117']
    for date in dataArr:
        # 
        # data = pro.moneyflow(trade_date=date, fields='ts_code,trade_date,net_mf_amount')
        data = pro.moneyflow(trade_date=date, fields='ts_code,trade_date,buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount')
        for codeInfo in data.values:
            code = codeInfo[0]
            # 大资金净流入
            # bigMoenyFlow = codeInfo[2]
            bigMoenyFlow = (codeInfo[2]-codeInfo[3]) + (codeInfo[4]-codeInfo[5])
            bigMonFlowArr = code_moneyflow.get(code)
            if bigMonFlowArr == None:
                bigMonFlowArr = [bigMoenyFlow]
            else:
                bigMonFlowArr.append(bigMoenyFlow)
            code_moneyflow[code] = bigMonFlowArr
    allCodes = list(code_moneyflow.keys())
    niceCode = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue
        if '600634' in code:
            print('ww')
        moneyFlowArr = code_moneyflow[code]
        isContinue = False
        for moneyFow in moneyFlowArr:
            if moneyFow <= 10:
                isContinue = True
                break
        if isContinue:
            continue
        niceCode.append(code)
    return niceCode
    
    # 逻辑：获取历史数据，按天去做排序
def getHistoryDataByDate():
    historyData = []
    dayNum = 10
    with open('/Users/chengpeng2/Desktop/choice/test.dat', 'r') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
            s = m.read(m.size())
            # 单引号转双引号
            bs = str(s, encoding = "utf8").replace('\'', '\"')
            # 去掉空格
            bs = bs.replace('\" ', '\"')
            dict = json.loads(bs)
            allStokeDate = {}
            allCodes = list(dict.keys())
            # 大涨，微涨跌[-0.5,1]，微涨跌[-0.5,1]，跌[-5,-2]
            for i in range(len(allCodes)):
                code = allCodes[i]
                dataArr = dict[code]
                toIndex = 0
                if dayNum == 0:
                    toIndex = len(dataArr)
                else:
                    toIndex = dayNum
                tempArr = dataArr[0:toIndex]
                for temp in tempArr:
                    for key in temp.keys():
                        if (key != 'ts_code') & (key != 'trade_date'):
                            temp[key] = float(temp[key])
                code = code.replace('.csv', '')
                allStokeDate[code] = tempArr
                
            return allStokeDate
    

if __name__ == "__main__":
    getHistoryDataByDate()
    # getQFQVerPrice()
    # 更新股票行情信息
    # getAllStokeInfo()

    # 每天都可以跑一次，把最新的日K数据拉取到本地
    # addNewData()
    # 每次开始做回归测试时，需要先本地数据全部读取到内存中，以便其他进场获取数据
    # getLocalData()

    # 从网络获取最近600天的数据保存在本地
    # getAllStokeData(500)
    # getLocalData()

    # getLowPriceMainMoney_3()