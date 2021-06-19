from numpy.core.numeric import allclose
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
from pathlib import Path

import platform

# g_currentDir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(g_currentDir + '/../../../')

# token = 'ed854a25065df86d7d0dddf9161abc26e7eff21ccd2ba4d0d3d3e28c' # 大鹏的token
token = '47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899' # 阿文的token


tu.set_token(token)
pro = tu.pro_api()
globalSys_Mac = platform.system().lower() == 'darwin'
print('当前操作系统:%s' % platform.system().lower())

# 逻辑：路径转换
def pathToSys(path):
    if globalSys_Mac:
        return path
    else:
        return path.replace('/', '\\')

# globalPath = pathToSys(os.getcwd() + '/Desktop/test/')
globalPath = pathToSys(os.getcwd() + '/')
if not globalSys_Mac:
    globalPath = 'C:\\Users\\Administrator\\Desktop\\股票数据\\'
globalDataPath = pathToSys(globalPath + 'test.dat')

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
    saveDir = pathToSys(globalPath + 'StokeInfo/')
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    path = pathToSys(saveDir + '行业信息' + '.csv')
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
    # getAllStokeInfo()
    saveDir = pathToSys(globalPath + 'StokeInfo/')
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    path = pathToSys(saveDir + "行业信息.csv")
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

# 读取本地所有股票名称和股票代码
def getCodeAndCodeName():
    saveDir = pathToSys(globalPath + 'StokeInfo/')
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    path = pathToSys(saveDir + "行业信息.csv")
    codeAndCodeName = {}
    with codecs.open(path, 'r', encoding='utf8') as fp:
        fp_key = csv.reader(fp)
        
        for csv_key in fp_key:
            csv_reader = csv.DictReader(fp, fieldnames=csv_key)
            for row in csv_reader:
                code = row['代码']
                codeAndCodeName[code] = row['名称']
    return codeAndCodeName

# 获得前一天的时间
def getPreDateAndUnixTime(dateUnixTime):
    currentUnixTime = dateUnixTime - 60 * 60 * 24 * 1
    return [unixTime2LocalDate(currentUnixTime, "%Y%m%d"), currentUnixTime]

# 获得后一天的时间
def getBackDateAndUnixTime(dateUnixTime):
    currentUnixTime = dateUnixTime + 60 * 60 * 24 * 1
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
    saveDir = pathToSys(globalPath + 'DayKLine/')
    if os.path.exists(saveDir):
        a = os.listdir(saveDir)
        
        for j in a:
            csv_storage = []
            # saveDir = globalPath + 'DayKLine/'
            path = pathToSys(saveDir+j)
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
    with open(globalDataPath, "w+") as f:
        f.write('\x00' * len(data))
 
    with open(globalDataPath, 'r+') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)) as m:
            m.write(data)
            m.flush()
            print('本地数据服务，已开启')
            # 通过while循环保证数据一直保存在内存中
            # while True:
            #     time.sleep(2)

# 逻辑：获取最近dayNum天的所有股票的数据
def getAllStokeData(dayNum):
    allStokeDate = getRecentData(0, 0, dayNum)
    reloadWriteDataToLocal(allStokeDate)
    print('%d交易数据下载完成' % dayNum)
    return allStokeDate

# 逻辑：往本地重写数据
def reloadWriteDataToLocal(allStokeData):
    print('清空本地缓存数据，开始往本地重写前复权数据')
    saveDir = pathToSys(globalPath + 'DayKLine/')
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    allCodes = list(allStokeData.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeData[code]
        path = saveDir + code + '.csv'
        symbolFile = open(path, 'w+', encoding='utf8')
        symbolFile.write('ts_code, trade_date, open, high, low, close, pre_close, pct_chg, vol\n')
        symbolFile.flush()
        for data in dataArr:
            s = '%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
                    code,
                    data['trade_date'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['pre_close'],
                    data['pct_chg'],
                    data['vol'],
                )
            symbolFile.write(s)
            symbolFile.flush()
    print('交易数据下载完成')

# 逻辑：写入新的交易日K数据
def writeNewDayData(dict):
    # 获取本地所有数据
    allLocalData = getLocalKLineData(0)

    # 将当前目录下的所有文件名称读取进来
    saveDir = pathToSys(globalPath + 'DayKLine/')
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
        symbolFile.write('ts_code, trade_date, open, high, low, close, pre_colse, pct_chg, vol\n')
        symbolFile.flush()
        # dataframe = pd.DataFrame({'a_name':a,'b_name':b})
        for data in allArr:
            s = '%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
                    code,
                    data['trade_date'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['pre_close'],
                    data['pct_chg'],
                    data['vol'],
                )
            symbolFile.write(s)
            symbolFile.flush()
    print('保存完成')


# 逻辑：获取最新几天的数据， time默认为0，time主要解决因停市导致数据没有的问题
def getRecentData(localUnix = 0, dayNum=0, time=0):
        
    currentTime = getCurrentUnixTime()
    dateAndUnix = getPreDateAndUnixTime(currentTime)

    if localUnix > 0:
        dateAndUnix = getBackDateAndUnixTime(localUnix)

    date = dateAndUnix[0]
    dateUnix = dateAndUnix[1]

    # if 1: #如果当天下午4点以后，则可以获得到当前数据
    #     date = unixTime2LocalDate(currentTime, "%Y%m%d")
    #     dateUnix = currentTime

    allStokeDate = {}
    # for循环获取每天的全部股票的交易信息
    tempTime = 0

    # 昨日的收盘价
    yesterdayClosePrice = 0
    # 需要重新更新本地数据的股票
    needUpdateLocalDataCodes = []
    # 获取本地最近一天数据
    allLocalData = getLocalKLineData(1)
    
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
                # 先把已经除权的股票全部更新完成之后，再去更新未除权的股票
                reloadGetQFQStokeDataUpdateLocal(needUpdateLocalDataCodes)
                return allStokeDate
            if time:
                tempTime += 1
                if tempTime > time:
                    # 先把已经除权的股票全部更新完成之后，再去更新未除权的股票
                    reloadGetQFQStokeDataUpdateLocal(needUpdateLocalDataCodes)
                    return allStokeDate
            # 获取日线行情  ------ https://www.waditu.com/document/2?doc_id=27
            # vol:成交量、pct_chg:涨跌幅
            data = pro.daily(trade_date=date, fields='ts_code, trade_date, open, high, low, close, pre_close, pct_chg, vol')

            dateAndUnix = getPreDateAndUnixTime(dateUnix)
            if localUnix:
                dateAndUnix = getBackDateAndUnixTime(dateUnix)

            date = dateAndUnix[0]
            dateUnix = dateAndUnix[1]
            if localUnix == 0:
                if len(data.values) == 0:
                    tempTime -= 1
                    continue

            for i in range(len(data.values)):
                stokeData = data.values[i]
                code = stokeData[0]
                if code in needUpdateLocalDataCodes:
                    continue

                dataArr = allStokeDate.get(code, [])

                # 首次，获取本地最近一天收盘价
                if len(dataArr) == 0:
                    localDataArr = allLocalData.get(code, [])
                    if len(localDataArr) == 0:
                        continue
                    yesterdayClosePrice = localDataArr[0]['close']
                else:
                    yesterdayClosePrice = dataArr[0]['close']
                # 昨日收盘价和当天昨日收盘价不一致，说明当天除权了
                if yesterdayClosePrice != stokeData[6]:
                    print('【%s】在【%s】进行了除权' % (code, stokeData[1]))
                    needUpdateLocalDataCodes.append(code)
                    continue
                
                dic = {}
                index = 1
                dic['trade_date'] = stokeData[index]
                dic['open'] = stokeData[index+1]
                dic['high'] = stokeData[index+2]
                dic['low'] = stokeData[index+3]
                dic['close'] = stokeData[index+4]
                dic['pre_close'] = stokeData[index+5]
                dic['pct_chg'] = stokeData[index+6]
                dic['vol'] = stokeData[index+7]
                
                # 时间越小，在数组位置约靠后
                if localUnix:
                    dataArr.insert(0, dic)
                else:
                    dataArr.append(dic)
                allStokeDate[code] = dataArr
    # 先把已经除权的股票全部更新完成之后，再去更新未除权的股票
    reloadGetQFQStokeDataUpdateLocal(needUpdateLocalDataCodes)
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
    allStokeDate = getRecentData(reTopUnix, 0, dateNum-1)
    if len(list(allStokeDate.keys())) > 0:
        # 开始往本地csv文件头部插入新的数据
        writeNewDayData(allStokeDate)

# 逻辑：重新获取复权的数据，并更新本地文件
def reloadGetQFQStokeDataUpdateLocal(codes):
    if len(codes):
        getQFQStokeData(codes)


# 逻辑：获得本地保存的数据的最新日期
def getReTopDate():
    print('getReTopDate123')
    saveDir = pathToSys(globalPath + 'DayKLine/')
    if os.path.exists(saveDir):
        a = os.listdir(saveDir)
        if '000001.SZ.csv' in a:
            j = '000001.SZ.csv'
            path = pathToSys(saveDir+j)
            # 剔除隐藏文件
            if j.startswith('.'):
                print('ww')
            with codecs.open(path, 'r', encoding='utf8') as fp:
                fp_key = csv.reader(fp)
                
                for csv_key in fp_key:
                    csv_reader = csv.DictReader(fp, fieldnames=csv_key)
                    for row in csv_reader:
                        csv_dict = dict(row)
                        return csv_dict[' trade_date']
    return ''

# 逻辑：获得本地最近dayNum天的交易日K线数据
def getLocalKLineData(dayNum):
    with open(globalDataPath, 'r') as f:
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
def getQFQStokeData(codes=[], startDate='', endDate=''):
    codeAndCodeName = getCodeAndCodeName()
    if len(codes) == 0:
        allCodes = getAllStokeCode()
        for code in allCodes:
            codeName = codeAndCodeName.get(code, '')
            if ('退' in codeName) | ('688' in code[:3]):
                continue
            codes.append(code)
    
    endDateUnix = getCurrentUnixTime()
    if '' == endDate:
        endDate = getCurrentDayDate()
    
    if '' == startDate:
        startDate = unixTime2LocalDate(endDateUnix - 200*24*60*60, "%Y%m%d")

    allStokeDate = {}
    needNum = len(codes)
    for code in codes:
        needNum -= 1
        codeName = codeAndCodeName.get(code, '')
        data = tu.pro_bar(ts_code=code, adj='qfq', start_date=startDate, end_date=endDate)
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
                dic['pre_close'] = stokeData[index+5]
                dic['pct_chg'] = stokeData[index+7]
                dic['vol'] = stokeData[index+8]
                
                # 时间越小，在数组位置约靠后
                dataArr.append(dic)
                allStokeDate[code] = dataArr
        
        print('%s数据保存完成，剩余%d个' % (codeName, needNum))
    reloadWriteDataToLocal(allStokeDate)

'''
code        = codeInfo[0]
trade_date  = codeInfo[1]
open        = codeInfo[2]
high        = codeInfo[3]
low         = codeInfo[4]
close       = codeInfo[5]
pct_chg     = codeInfo[8]
vol         = codeInfo[9]
'''
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
    with open(globalDataPath, 'r') as f:
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

# 逻辑：获取最近几周周线数据, 偏移默认为0
def getRecentWeekData(weekNum, pre_move=0):
    # 返回的数据格式为字典，key为股票代码，value为该股票数组数据
    allStokeDate = {}

    # 第一步：找000001.SZ的最近所有周线交易日期
    allWeekTradeDate = []
    df = pro.weekly(ts_code='000001.SZ', fields='ts_code, trade_date')
    if len(df.values) != 0:
        for stokeData in df.values:
            allWeekTradeDate.append(stokeData[1])

    # 第二步：遍历最近几周的日期，获取所有股票信息
    for date in allWeekTradeDate[pre_move:weekNum+pre_move]:
        allData = pro.weekly(trade_date=date, fields='ts_code, trade_date, open, high, low, close, pct_chg, vol')
        if len(allData.values) != 0:
            for stokeData in allData.values:
                code = stokeData[0]
                dataArr = allStokeDate.get(code, [])
                dic = {}
                index = 1
                dic['trade_date'] = stokeData[1]
                dic['open'] = stokeData[index+1]
                dic['high'] = stokeData[index+2]
                dic['low'] = stokeData[index+3]
                dic['close'] = stokeData[index+4]
                dic['pct_chg'] = (stokeData[index+5])*100
                dic['vol'] = stokeData[index+6]
                
                # 时间越小，在数组位置约靠后
                dataArr.append(dic)
                allStokeDate[code] = dataArr

    return allStokeDate
    

if __name__ == "__main__":
    print('需要创建的文件路径%s'% globalPath)
    if not os.path.exists(globalPath):
        print('首次运行，创建路径文件')
        os.makedirs(globalPath)
    else:
        print('非首次运行，不需要创建路径文件')


    # getHistoryDataByDate()
    # getAllStokeData(5)

    # 更新股票行情信息
    getAllStokeInfo()
    # getRecentWeekData(4, 0)

    # 每天都可以跑一次，把最新的日K数据拉取到本地
    # addNewData()

    
    # 从网络获取最近120天的前复权数据保存在本地
    getQFQStokeData()
    
    # 每次开始做回归测试时，需要先本地数据全部读取到内存中，以便其他进场获取数据
    getLocalData()
    print('文件保存路径:%s' % globalPath)
    # getLowPriceMainMoney_3()