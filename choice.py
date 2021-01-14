# 目的：通过软件筛选出进入低谷期的股票，然后买它

import tushare as tu
import time
import datetime
import numpy as np
import Stoke
import mmap
import contextlib
import json

'''
保存最近5年A股所有的日K线数据

1、找到前多少天连续涨停
2、通过市值筛选超过100亿的股票
3、找到换手率高的票
4、找到前15天左右成交量平稳，之后成交量突然上升的票（从交易量相对于前15天放大的那一天，就开始一路上涨了）
5、找到当天比前五天平均成交量高3倍以上的股，且当天是涨的
6、通过分时成交数据的成交量和单数，可以找到大单
7、条件：可以根据市值，换手率（成交量/总股本）、股票单价


8、当天涨停，交易量比前几天都高3倍以上，但是换手率不到4%，前几天都是下跌趋势，这只股票可能第二天继续涨停
'''

token = 'ed854a25065df86d7d0dddf9161abc26e7eff21ccd2ba4d0d3d3e28c'
tu.set_token(token)
pro = tu.pro_api()
path = '/Users/hock/Stock/'

# 逻辑：取所有只股票最近三个月最高价比最低价贵30%
# 获取某只股的最新收盘价
        # newPrice = pro.daily(ts_code=code, start_data=todayData, end_data=todayData, fields='close').values[0][0]
        # df = pro.daily(ts_code=code, start_date='20200420', end_date='20200524', fields='close')
        # if maxPrice == 0:
        #     maxPrice = df.values.max()

        # if ((maxPrice-newPrice)/newPrice) > 0.3:



# 逻辑：从所有股票中选取 最近n天连续涨停的股票
def getRecentlimitup(dayNum):
    # 记录连续dayNum涨停的股票
    allStokeDate = getLocalKLineData(30)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if isNeedDelCode(code):
            continue
        if len(allStokeDate[code]) < 30:
            # print("这是一直新上市的股票%s" % code)
            continue
        dataArr = allStokeDate[code][0:dayNum]
        for j in range(len(dataArr)):
            chg = dataArr[j]['pct_chg']
            if chg < 9.9:
                break
            if j == len(dataArr) - 1:
                limitUpCodes.append(code)
    print('===============以下是：从所有股票中选取 最近n天连续涨停的股票===============')
    for code in limitUpCodes:
        print(code)
'''
【1】今天封板涨停
'''
def limitupFB(dayNum):
    # 记录连续dayNum涨停的股票
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if isNeedDelCode(code):
            continue
        if len(allStokeDate[code]) < dayNum:
            # print("这是一直新上市的股票%s" % code)
            continue
        dataArr = allStokeDate[code][0:dayNum]
        if dataArr[0]['pct_chg'] < 9.7:
            continue
        if (dataArr[0]['open'] == dataArr[0]['low']) & (dataArr[0]['open'] == dataArr[0]['close']):
            limitUpCodes.append(code)
    print('===============以下是：今天封板涨停的股票===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：第一天涨幅超过9.8，第二天微涨在[-4~9]之间，但是收盘低于开盘
def ZwZ():
    allStokeDate = getLocalKLineData(2)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if isNeedDelCode(code):
            continue
        dataArr = allStokeDate[code]
        if len(dataArr) < 2:
            continue

        if dataArr[1]['pct_chg'] < 9.8:
            continue
        # 第二天微涨，但是收盘低于开盘
        if (dataArr[0]['pct_chg'] < -4.5) | (dataArr[0]['pct_chg'] > 9):
            continue
        if dataArr[0]['close'] < dataArr[0]['open']:
            limitUpCodes.append(code)
    print('===============以下是：第一天涨幅超过9.8，第二天微涨在[-4~9]之间，但是收盘低于开盘===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：剔除300，688
def isNeedDelCode(code):
    if (code[0:3] == '300') | (code[0:3] == '688'):
        return True
    return False

# 逻辑：获得list里面的最高价
def getMaxHighPrice(dataArr):
    maxPrice = 0
    for data in dataArr:
        if maxPrice < data['high']:
            maxPrice = data['high']
    return maxPrice

    # 逻辑：获得list里面的最高价
def getMaxClosePrice(dataArr):
    maxPrice = 0
    for data in dataArr:
        if maxPrice < data['close']:
            maxPrice = data['close']
    return maxPrice
# 逻辑：把数组里面的数据组成字符串
def getStrWithList(list):
    str = ''
    for code in list:
        if len(str) == 0:
            str = code
        else:
            str += ',' + code
    return str

# 设置保留几位小数，不做4舍5入处理
def cut(num, n):
    numStr = str(num)
    a, b, c = numStr.partition('.')
    c = (c+"0"*n)[:n]
    return float(".".join([a, c]))

# 逻辑：取两个数组中，相同的元素
def getSomeItemWithList(list_1, list_2):
    codeDic = {}
    for code in list_1:
        num = codeDic.get(code)
        if num == None:
            num = 0
        num += 1
        codeDic[code] = num
    
    for code in list_2:
        num = codeDic.get(code)
        if num == None:
            num = 0
        num += 1
        codeDic[code] = num
    
    someCodes = []
    for code in codeDic.keys():
        num = codeDic.get(code)
        if num == 2:
            someCodes.append(code)
    return someCodes

# 逻辑：筛选市值超过100亿的股
def marketCapAboveBillion(codes):
    needCodes = []
    for code in codes:
        needCodes.append(code)
        print(code)
    return needCodes

# 逻辑：根据股票代码获得当天涨跌幅
def getCurrentChange(codes):
    currentDate = unixTime2LocalDate(getCurrentUnixTime(), "%Y%m%d")
    # currentDate = unixTime2LocalDate(getCurrentUnixTime(), "20200814")
    datas = pro.daily(ts_code=codes, start_date=currentDate, end_date=currentDate, fields='ts_code, pct_chg')
    deCodes = []
    BigZCodes = []
    for data in datas.values:
        print(data)
        if data[1] < 0:
            deCodes.append(data[0])
        if data[1] > 2:
            BigZCodes.append([data[0], data[1]])
    print('跌的比例： %f' % (len(deCodes)/len(datas.values)))
    print('大涨的比例：%f' % (len(BigZCodes)/len(datas.values)))

# 逻辑：筛选换手率高的
def getTurnoverRateMax():
    return 0

# 逻辑：获取float数据
def getFValue(data, key):
    return float(data[key])

# 逻辑：找到前段时间交易量一般，最近交易量增加的票
# 思路：通过字典存每只股票，最近dayNum天的成交量数据，从当天时间往之前时间遍历成交量数组，如果之后的数据呈现下降的趋势，说明最近这只股成交量再上升
def getVolIncrease(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    allCodes = deleteCodes(allCodes)
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        # 计算数组中从1到最后一位元素总数的平均值
        
        if len(dataArr) == 0:
            continue

        if (len(dataArr) < dayNum) | (dataArr[0]['pct_chg'] < 6):
            continue

        # 如果当天的交易量不超过3%，则剔除掉
        # if dataArr[0]['vol'] / (总股本) < 0.03:
        # continue
        # 剔除股价低于2块，高于100块
        if (dataArr[0]['close'] <= 2) | (dataArr[0]['close'] >= 100):
            continue

        # 当天(最高价-开盘价) / (收盘价 - 开盘价)，说明是买方弱,卖方强，涨上去又跌下来，剔除该股
        if (dataArr[0]['close'] - dataArr[0]['open']) == 0:
            continue

        if (dataArr[0]['high'] - dataArr[0]['open']) / (dataArr[0]['close'] - dataArr[0]['open']) >= 2:
            continue

        volArr = []
        
        isContinue = 0
        for dic in dataArr[1:]:
            # for遍历当天的交易量比之前每天交易量都要高出2倍
            if dataArr[0]['vol'] / dic['vol'] < 2:
                isContinue = 1
                break
            volArr.append(dic['vol'])
        if isContinue : 
            isContinue = 0
            continue
        averageVol = calAverage(volArr)

        # 上一天比上上天交易量高2倍或者上一天涨幅超过3个点，说明这只股已经倍提前买进，可以剔除
        if ((dataArr[1]['vol'] / dataArr[2]['vol']) >= 2) | (dataArr[1]['pct_chg'] >= 2):
            continue

        # if getDayKLine(code, 180) == False:
        #     continue

        # 找到第1、2天大涨，第3天大跌，4，5，6，7天走势是跌，涨幅不超过1%，之后可能大涨

        # 跌(<-1)跌(<-1)跌(<-1)涨(<1),第五天涨

        if (dataArr[0]['vol'] / averageVol) >= 3:
            limitUpCodes.append(code)
    print('===============以下是：找到前段时间交易量一般，最近交易量增加的票===============')
    for code in limitUpCodes:
        print(code)

# 获得前一天的时间
def getPreDateAndUnixTime(dateUnixTime):
    currentUnixTime = dateUnixTime - 60 * 60 * 24 * 1
    return [unixTime2LocalDate(currentUnixTime, "%Y%m%d"), currentUnixTime]



# 资金流动 --- 接口报错：抱歉，您没有访问该接口的权限，权限的具体详情访问
def getMoneyFlow():
    df = pro.moneyflow(ts_code='002149.SZ', start_date='20190314', end_date='20190315')
    print(df)

def getCurrentDayDate():
    return time.strftime("%Y%m%d", time.localtime(time.time()))

def getCurrentUnixTime():
    return int(time.mktime(datetime.datetime.now().timetuple()))

# 逻辑：是否是封板涨停
def isFengZT(data):
    if (data['pct_chg'] > 9.9) & (data['open'] == data['low']) & (data['close'] == data['low']):
        return True
    return False
# date字符串转Unix时间
def date2UnixTime(dt):
    #转换成时间数组 %Y-%m-%d %H:%M:%S
    timeArray = time.strptime(dt, "%m-%d %H:%M:%S")
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

# 逻辑：给定一个数组。判断数组数据是上涨、平稳、下跌哪种趋势
def getListTrend(datas):
    if len(datas) < 2:
        return
    # 先比较数组首尾数据大小，得出是涨还是跌
    # 定义一个浮动比例
    trend = 0.05
    if calChange(datas[0], datas[-1]) > trend: #涨
        return '涨'
    elif calChange(datas[0], datas[-1]) < -trend: #跌:
        return '跌'        
    else:
        return '无'

# 逻辑：计算两个数之差的比例: (收盘价-开盘价) / 开盘价
def calChange(num1, num2):
    return (num2 - num1) / num1

# 逻辑：计算数组的平均值
def calAverage(datas):
    if len(datas) == 0:
        return
    total = 0
    for data in datas:
        total += data
    return total / len(datas)

# 逻辑：计算日K数据的平均值
def calDayAverage(dayDatas):
    if len(dayDatas) == 0:
        return
    total = 0
    for data in dayDatas:
        total += data['close']
    return total / len(dayDatas)

# 逻辑：获得数据中的最大值
def getMaxInList(datas, key):
    keyMax = 0
    for data in datas:
        if data[key] > keyMax:
            keyMax = data['close']
    return keyMax
        
# 逻辑：判断是否属于深A，沪A，创业板
def deleteCodes(codes):
    newCodes = []
    for code in codes:
        symbol = code[0:3]
        # 删除科创板股票、创业板
        if (symbol != '688') & (symbol != '300'):
            newCodes.append(code)
    return newCodes

# 逻辑：查询某只股票最近多少天的日K数据,
def getDayKLine(code, day):
    currentTime = getCurrentUnixTime()
    endDate = unixTime2LocalDate(currentTime, "%Y%m%d")
    startDate = unixTime2LocalDate(currentTime - 60 * 60 * 24 * day, "%Y%m%d")
    datas = pro.daily(ts_code=code, start_date=startDate, end_date=endDate, fields='close, pct_chg')
    # 查询某只股票最近15个交易日天内如果有跌幅超过9%，说明这只股很危险，
    highClose = 0
    todayClose = 0
    allClose = 0
    times = 0
    for data in datas.values:
        times += 1
        if todayClose == 0:
            todayClose = data[0]
        if (data[1] <= -8) & (times <= 15):
            return False
        if highClose < data[0]:
            highClose = data[0]
        allClose += data[0]
    
    # (今收 - 近day天平均收盘价) / 近day天平均收盘价 > 0.8
    if ((todayClose - allClose/day) / (allClose/day) > 0.8):
        return False

    # if highClose == todayClose:
        # return False

    return True

# [涨，跌，跌，跌，跌]找到这类股票
def getZddddStoke(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # [涨，跌，跌，跌，跌]找到这类股票
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        if dataArr[0]['pct_chg'] < 5:
            continue
        if dataArr[1]['pct_chg'] > 0:
            continue
        if dataArr[2]['pct_chg'] > 0:
            continue
        if dataArr[3]['pct_chg'] > 0:
            continue
        if dataArr[4]['pct_chg'] > 0:
            continue
        limitUpCodes.append(code)
    print(limitUpCodes)

# [涨，跌，不变，未知，未知]找到这类股票
# 逻辑：先找涨停的，后一天大跌的，后一天涨跌幅很小
def getZdowwStoke(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # [>=7%，(-5% ~ -2%)，(-2% ~ 2%)，未知，未知]
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        if (dataArr[1]['pct_chg'] < -2) | (dataArr[1]['pct_chg'] > 2):
            continue
        if (dataArr[2]['pct_chg'] >= -2) | (dataArr[2]['pct_chg'] <= -5):
            continue
        if dataArr[3]['pct_chg'] < 7:
            continue
        limitUpCodes.append(code)
    print(limitUpCodes)

# [涨，跌，未知]且后一天 收盘>开盘，收盘 > 后一天收盘，开盘 < 后一天收盘
def getZdwStoke(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # [>=7%，(-5% ~ -2%)，未知，未知]
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        dayOne = dayNum - 2

        if dataArr[dayOne-1]['pct_chg'] > -1:
            continue

        pre_1_open = dataArr[dayOne]['open']
        pre_1_chg = dataArr[dayOne]['pct_chg']
        pre_1_close = dataArr[dayOne]['close']
        pre_1_high = dataArr[dayOne]['high']

        pre_2_open = dataArr[dayOne+1]['open']
        pre_2_chg = dataArr[dayOne+1]['pct_chg']
        pre_2_close = dataArr[dayOne+1]['close']
        pre_2_high = dataArr[dayOne+1]['high']
        # (前天最高价-前天收盘价) / 前天开盘价：可以算出超出蜡烛线的比例，超过1.5%则提出该支股票
        if (pre_2_high-pre_2_close)/pre_2_open > 0.015:
            continue
        # 前天大涨7个点以上，昨天跌了，昨天收盘>昨天开盘，前天开盘<昨天开盘，前天收盘>昨天收盘，(昨天最高价-前天收盘价)/前天收盘价 < 0.02
        if  (pre_2_chg > 7) & (pre_1_chg < 0) & (pre_1_close > pre_1_open) & (pre_2_open < pre_1_open) & (pre_2_close > pre_1_close) & ((pre_1_high - pre_2_close)/pre_2_close < 0.06):
            limitUpCodes.append(code)
    print(limitUpCodes)

# [涨，微涨，未知]
def getZzwStoke(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes1 = []
    limitUpCodes2 = []
    limitUpCodes3 = []
    allCodes = list(allStokeDate.keys())

    # [>=9%，(-2% ~ 0%)，未知]
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        if isGoodCandle(dataArr[0], False):
            print(dataArr[0])
            continue

        dayOne = dayNum - 2

        pre_1_open = dataArr[dayOne]['open']
        pre_1_chg = dataArr[dayOne]['pct_chg']
        pre_1_close = dataArr[dayOne]['close']
        pre_1_high = dataArr[dayOne]['high']

        pre_2_open = dataArr[dayOne+1]['open']
        pre_2_chg = dataArr[dayOne+1]['pct_chg']
        pre_2_close = dataArr[dayOne+1]['close']
        pre_2_high = dataArr[dayOne+1]['high']
        # (前天最高价-前天收盘价) / 前天开盘价：可以算出超出蜡烛线的比例，超过1.5%则提出该支股票
        # [>=9%，(-2% ~ 0%)，未知]
        # if (pre_2_chg >= 9) & (pre_1_chg >= -2) & (pre_1_chg < 0):
            # limitUpCodes1.append(code)

        # [>=9%，(0% ~ 2%)，未知]
        # if (pre_2_chg >= 9) & (pre_1_chg > 0) & (pre_1_chg < 2):
            # limitUpCodes2.append(code)

        # [>=9%，(2% ~ 5%)，未知]
        # if (pre_2_chg >= 9) & (pre_1_chg >= 2) & (pre_1_chg < 5) & (pre_1_open > pre_1_close):
        if (pre_2_chg >= 8) & (pre_1_chg > 0) & (pre_1_open > pre_1_close):
            print([code, dataArr[dayOne-1]['pct_chg']])
            # limitUpCodes3.append([code, dataArr[dayOne+1]['pct_chg']])
    # print(limitUpCodes1)
    # print('************************\n')
    # print(limitUpCodes2)
    # print('************************\n')
    print('************************\n')
    # for codes in limitUpCodes3:
    #     getCurrentChange(codes)
    # print(limitUpCodes3)

# 逻辑：大涨，微涨跌[-0.5,1]，微涨跌[-0.5,1]，跌[-5,-2]，看第五天的数据如何
def ZwwdT(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 大涨，微涨跌[-0.5,1]，微涨跌[-0.5,1]，跌[-5,-2]
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        # if code == '600330.SH':
        #     print('www')
        if len(dataArr) < dayNum:
            continue
        if (dataArr[-1]['pct_chg'] < 7):
            continue
        
        if (dataArr[-2]['pct_chg'] < -0.5) | (dataArr[-2]['pct_chg'] > 1):
            continue
    
        if (dataArr[-3]['pct_chg'] < -0.5) | (dataArr[-3]['pct_chg'] > 1):
            continue

        if (dataArr[-4]['pct_chg'] <= -5) | (dataArr[-4]['pct_chg'] >= -2):
            continue
    
        if dDaoChui(dataArr[-4]):
            continue

        limitUpCodes.append(code)

    print(limitUpCodes)


# 逻辑：判断是否是不错的蜡烛线
def isGoodCandle(data, isIncrease):
    # (高-收)/收 * 2 < (收-开)/开 & (开-低)/低 * 2 < ((收-开)/开)
    openP = data['open']
    closeP = data['close']
    highP = data['high']
    lowP = data['low']
    
    if isIncrease:
        # OCchg:(收-开)/开
        OCchg = calChange(data['open'], data['close'])
        if (closeP > openP) & ((calChange(closeP, highP) * 2) < OCchg) & ((calChange(lowP, openP) * 2) < OCchg):
            return True
    else:
        # OCchg:(开-收)/收
        OCchg = calChange(data['close'], data['open'])
        if (closeP < openP) & ((calChange(openP, highP) * 2) < OCchg) & ((calChange(lowP, closeP) * 2) < OCchg):
            return True
    return False

# 逻辑：判断是否是跌倒锤子
def dDaoChui(data):
    # 跌，(高-开)/开 > (开-收)/收，(高-开)/开 > 3
    if (data['pct_chg'] < 0) & (calChange(data['open'], data['high']) > calChange(data['close'], data['open'])) & (calChange(data['open'], data['high']) > 0.03):
        return True
    return False

# 逻辑：前两天大涨，后两天大跌
def ZZDD(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 大涨，大涨，大跌，大跌
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        if (dataArr[-1]['pct_chg'] > 9) & (dataArr[-2]['pct_chg'] > 9) & (dataArr[-3]['pct_chg'] < -6) & (dataArr[-4]['pct_chg'] < -5):
            limitUpCodes.append([code, dataArr])
    print(limitUpCodes)
    print('*******************************')
        
# 逻辑：获得本地最近dayNum天的交易日K线数据
def getLocalKLineData(dayNum):
    fileUrl = path + 'test.dat'
    with open(fileUrl, 'r') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
            s = m.read(m.size())
            # 单引号转双引号
            bs = str(s, encoding = "utf8").replace('\'', '\"')
            # 去掉空格
            bs = bs.replace('\" ', '\"')
            dict = json.loads(bs)
            allStokeDate = {}
            allCodes = list(dict.keys())

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

# 逻辑：第一天大涨，第二天大跌，看第三天结果
def ZDN(isLocal, dayNum):
    allStokeDate = {}
    if isLocal:
        allStokeDate = getLocalKLineData(dayNum)
    else:
        allStokeDate = Stoke.getRecentData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 第一天大涨，第二天大跌，看第三天结果,找到这类股票
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        if (len(dataArr) == 0) | (len(dataArr) < dayNum):
            continue
        min_day = dayNum
        time = int(len(dataArr)/min_day) if len(dataArr)%min_day == 0 else int(len(dataArr)/min_day)+1
        codeArr = []
        for i in range(time):
            if ((time-i)*min_day > len(dataArr)) | ((time-i) < 0):
                break
            # 第一天大涨，涨幅超过8个点
            if dataArr[(time-i)*min_day - 1]['pct_chg'] < 8:
                continue
            # 第二天大跌，跌幅超过5个点
            if dataArr[(time-i)*min_day - 2]['pct_chg'] > -2:
                continue
            # 第三天涨跌幅不超过1个点
            if (dataArr[(time-i)*min_day - 3]['pct_chg'] < -1) | (dataArr[(time-i)*min_day - 2]['pct_chg'] > 1):
                continue
            # 第四天跌幅超过3个点
            if dataArr[(time-i)*min_day - 4]['pct_chg'] > -2:
                continue    
            codeArr.append([code, dataArr[(time-i)*min_day - min_day]['pct_chg'], dataArr[(time-i)*min_day - min_day]['trade_date']])
            i += min_day
        if len(codeArr):
            print(codeArr)
            limitUpCodes.append(codeArr)

    time = 0
    # 涨的次数 >0
    z_time = 0
    # 大涨的次数 >5
    dz_time = 0
    # 跌的次数 < 0
    d_time = 0
    # 大跌的次数 <-5
    dd_time = 0
    for datas in limitUpCodes:
        for data in datas:
            time += 1
            if data[1] > 0:
                z_time += 1
                if data[1] > 5:
                    dz_time += 1
            elif data[1] < 0:
                d_time += 1
                if data[1] < -5:
                    dd_time += 1
    print('总共有%s条数据' % time)
    print('涨有%s条数据' % z_time)
    print('大涨有%s条数据' % dz_time)
    print('跌有%s条数据' % d_time)
    print('大跌有%s条数据' % dd_time)
'''
回归测试：
1、所有数据 
2、测试逻辑
'''

# 逻辑：第一大跌，第二天出现小涨幅且上影线长，下影线短，上影线比身体长(线形态)
def dZTopLBottomS():
    allStokeDate = getLocalKLineData(2)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < 2:
            continue
        
        dataArr = allStokeDate[code]        
        # 第一天大跌，跌幅超过3个点
        if dataArr[1]['pct_chg'] > -5:
            continue
        # 第二天涨幅在0-3个点之间
        if (dataArr[0]['pct_chg'] > 3) | (dataArr[0]['pct_chg'] < 0):
            continue
        # 第二天上影线长，下影线短，上影线比身体长
        if topLongBottomShort(dataArr[0], False) == False:
            continue
        limitUpCodes.append(code)
    print('===============以下是：第一大跌，第二天出现小涨幅且上影线长，下影线短，上影线比身体长(K线形态)===============')
    for code in limitUpCodes:
        print(code)
    return limitUpCodes

# 逻辑：上影线长，下影线短，上影线比身体长
def topLongBottomShort(data, isIncrease):
    open = data['open']
    low = data['low']
    high = data['high']
    close = data['close']
    chg = data['pct_chg']
    if isIncrease:
        # 涨
        if (chg > 0) & ((high-close) > 2 * (open-low)) & ((high-close) > (close - open)) & (open > low) & ((high-close) > 2 * (close-open)) :
            return True
        else:
            return False
    else:
        if (chg < 0) & ((high-open) > 2 * (close-low)) & ((high-open) > (open - close)) & (close > low) & ((high-open) > 2 * (open-close)) :
            return True
        return False
        # 跌

# 逻辑：中轨线(MB)，取最近20天的收盘价之和除以20，得出20天的平均价
# 计算方式：
def calMB(datas):
    total = 0
    for data in datas:
        total += data['close']
    return total/20

# 逻辑：标准差(MD)
# 计算方式：平方根20天的(close - MA)的两次方之和除以20
def calMD(datas, mb):
    total = 0
    for data in datas:
        total += (data['close'] - mb) * (data['close'] - mb)
    return (total/20) ** 0.5

# 逻辑：上轨线(UP)
# 计算方式
def calUP(mb, md):
    return mb + 2*md

# 逻辑：下轨线(DN)
# 计算方式
def calDN(mb, md):
    return mb - 2*md

# 逻辑：极限宽指标(WIDTH)
# 计算方式
def calWIDTH(up, dn, mb):
    if mb == 0:
        return 0.0
    return (up - dn) / mb

'''
【1】第一天跌，开盘收盘都低于中轨线
【2】第二天开盘价，收盘价都低于中轨线，且第二天涨幅在0-4之间
【3】第三天开盘价低于中轨线，收盘价高于中轨线，且低于上轨线，且第三天涨幅大于0
'''
# 计算6月30日的MB，UP，DN的值（该策略适合股市平稳时，boll线追涨策略）
def calMbUpDn():
    allStokeDate = getLocalKLineData(22)
    allCodes = list(allStokeDate.keys())
    needCodes = []
    codeAndChgWidth = {}
    num = 0
    for i in range(len(allCodes)):
        code = allCodes[i]
        datas = allStokeDate[code][0:20]
        if len(allStokeDate[code]) != 22:
            continue
        mb = calMB(datas)
        md = calMD(datas, mb)
        up = calUP(mb, md)
        dn = calDN(mb, md)
        width = calWIDTH(up, dn, mb)

        datas_pre_1 = allStokeDate[code][1:21]
        mb_pre_1 = calMB(datas_pre_1)
        md_pre_1 = calMD(datas_pre_1, mb_pre_1)
        up_pre_1 = calUP(mb_pre_1, md_pre_1)
        dn_pre_1 = calDN(mb_pre_1, md_pre_1)

        datas_pre_2 = allStokeDate[code][2:22]
        mb_pre_2 = calMB(datas_pre_2)
        md_pre_2 = calMD(datas_pre_2, mb_pre_2)
        up_pre_2 = calUP(mb_pre_2, md_pre_2)
        dn_pre_2 = calDN(mb_pre_2, md_pre_2)

        # 暂时去掉极限差<0.1
        # if (width > 0.1):
        #     continue
        
        # if code[0:6] == '002469':
        #     print('www')

        if (len(datas) < 3):
            continue
        # 第三天开盘价低于中轨线，收盘价高于中轨线，且低于上轨线，且第三天涨幅大于0
        if (datas[0]['open'] >= mb) | (datas[0]['close'] >= up) | (datas[0]['close'] <= mb) | (datas[0]['pct_chg'] <= 0):
            continue

        # 可以考虑第二天交易量>第一天交易量

        # 第二天开盘价，收盘价都低于中轨线，且第二天涨幅在0-4之间
        if (datas[1]['open'] < mb_pre_1) & (datas[1]['close'] < mb_pre_1) & (datas[1]['pct_chg'] > 0) & (datas[1]['pct_chg'] < 4):
            # 第一天跌，开盘收盘都低于中轨线
            if (datas[2]['pct_chg'] < 0) & (datas[2]['close'] < mb_pre_2):
                # needCodes.append([code, width])
                needCodes.append(code)
                info = {}
                info['pct_chg'] = datas[0]['pct_chg']
                info['width'] = width
                codeAndChgWidth[code] = info
    newCodes = deleteCodes(needCodes)[:100]
    codeStr = getStrWithList(newCodes)
    codeAllInfo = Stoke.get_daily_basic(codeStr)
    
    for key in codeAllInfo.keys():
        codeInfo = codeAllInfo[key]
        chgAndWidth = codeAndChgWidth[key]
        codeInfo['pct_chg'] = chgAndWidth['pct_chg']
        codeInfo['width'] = chgAndWidth['width']
        print ('代码:%s, 简称:%s, 涨幅:%.2f, PE:%.2f, 市值:%.2f, 极限差:%.2f' % (key, codeInfo['name'], codeInfo['pct_chg'], codeInfo['pe'], codeInfo['total_mv'], codeInfo['width']))
    # print('上轨线up = %0.2f' % up)
    # print('中轨线mb = %0.2f' % mb)
    # print('下轨线dn = %0.2f' % dn)calMbUpDn
    # print('极限宽指标width = %0.2f' % width)
    print('#################################')
 
# 逻辑：找到最近两天跌的股票
def recentTwoDayD(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 跌，跌
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        if (dataArr[0]['pct_chg'] < -2) & (dataArr[1]['pct_chg'] < -2):
            limitUpCodes.append([code, dataArr[0]['pct_chg']])
    for code in limitUpCodes:
        print(code)

# 逻辑：找最近几天没有放量大跌的股，看之后几天的走势
def getRecentNoBigVolBidDie(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
        if (dataArr[0]['pct_chg'] < -6) & ((dataArr[0]['pct_chg'] > -9)) & (calChange(dataArr[1]['vol'], dataArr[0]['vol']) < 0.18):
            limitUpCodes.append([code, dataArr[0]['trade_date']])
    print('===============以下是：找最近几天没有放量大跌的股，看之后几天的走势===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：找到最近两天涨停，第三天大跌的股票
def recentTwoDayZOneD(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 涨，涨，跌
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        if (dataArr[0]['pct_chg'] < -8):
            if (dataArr[1]['pct_chg'] > 9) & (dataArr[2]['pct_chg'] > 9):
                limitUpCodes.append([code, dataArr[0]['pct_chg']])
    print('===============以下是：找到最近两天涨停，第三天大跌的股票===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：第一天涨幅超过2个点，第二天大跌5个点以上，第二天交易量比第一天还低
def zDVollow(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 涨，跌
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        if (dataArr[0]['pct_chg'] < -5) & (dataArr[1]['pct_chg'] > 2) & (dataArr[0]['vol'] < dataArr[1]['vol']):
            limitUpCodes.append([code, dataArr[0]['trade_date']])
    print('===============以下是：第一天涨幅超过2个点，第二天大跌5个点以上，第二天交易量比第一天还低===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：第一天跌幅超过2个点，第二天大跌5个点以上，第二天交易量比第一天还低
def dDVollow(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    # 从数据中找到第一个比后面的数据的平均值高3倍
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    # 涨，跌
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        if (dataArr[0]['pct_chg'] < -5) & (dataArr[1]['pct_chg'] < -1.5) & (dataArr[1]['pct_chg'] > -4) & (dataArr[0]['vol'] < dataArr[1]['vol']):
            limitUpCodes.append([code, dataArr[0]['trade_date']])
    print('===============以下是：第一天跌幅超过2个点，第二天大跌5个点以上，第二天交易量比第一天还低===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：找到第一天开盘价低于中位线，第二天收盘价高于中位线(Boll线策略)
def lowMTopM(dayNum):
    allStokeDate = getLocalKLineData(dayNum+19)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    
    # 策略初步选出
    needCodes = []
    # 选出涨
    zCodes = []
    # 选出大涨
    dzCode = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum+19:
            continue
        
        mb_one = calMB(dataArr[1:])
        mb_two = calMB(dataArr[:-1])

        if (dataArr[0]['close'] > mb_two) & (dataArr[1]['open'] < mb_one):
            needCodes.append(code)
            # 当天涨，且开盘价低于中轨线
            if (dataArr[0]['pct_chg'] > 0) & (dataArr[0]['open'] < mb_two):
                zCodes.append(code)
                if dataArr[0]['pct_chg'] > 5:
                    dzCode.append(code)
            limitUpCodes.append(code)
    print('===============以下是：找到第一天开盘价低于中位线，第二天收盘价高于中位线(Boll线策略)===============')
    # print('跌:%f' % (1 - (len(zCodes)/len(needCodes))))
    # print('涨:%f' % (len(zCodes)/len(needCodes)))
    # print('大涨:%f' % (len(dzCode)/len(needCodes)))
    # 分析大涨，涨，跌的区别
    for code in dzCode:
        print(code)
    return limitUpCodes

# 逻辑：找最近5天两次涨停的股票
def ZTTwo(dayNum):
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    
    # 策略初步选出
    needCodes = []
    # 选出涨
    zCodes = []
    # 选出大涨
    dzCode = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
        
        ztTime = 0
        for data in dataArr:
            if (data['pct_chg'] > 9.9) & (dataArr[0]['pct_chg'] > 9.9) & (dataArr[1]['pct_chg'] < 9):
                ztTime += 1
                if ztTime == 2:
                    limitUpCodes.append(code)
                    continue
    for code in limitUpCodes:
        print(code)

# 逻辑：找连续2天封板涨停的股票
def getTwoDayZT():
    dayNum = 2
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
    
        if (dataArr[0]['pct_chg'] > 9.9) & (dataArr[1]['pct_chg'] > 9.9) & (dataArr[0]['open'] == dataArr[0]['close']) & (dataArr[1]['open'] == dataArr[1]['close']):
            limitUpCodes.append(code)
    print('===============以下是：找连续2天封板涨停的股票,找到回调的机会上车===============')
    for code in limitUpCodes:
        print(code)
'''
【1】第一天涨停，前十天未涨停的股
【2】第二天大跌的，跌幅超过6个点，看第三天的数据
'''
def getZTwoDie():
    dayNum = 30
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    num = 0
    isTest = True
    for i in range(10):
        limitUpCodes = []
        if isTest:
            num = 3+i
        for i in range(len(allCodes)):
            code = allCodes[i]
            if (code[0:3] == '300') | (code[0:3] == '688'):
                continue
            dataArr = allStokeDate[code]

            if len(dataArr) < dayNum:
                continue

            if dataArr[num]['pct_chg'] < 9.9:
                continue

            # 【2】当天收盘价 * 1.02 > 最近20个交易日的最高价
            if dataArr[num]['close'] * 1.02 < getMaxHighPrice(dataArr[num+1:num+1+20]):
                continue
            # 第二天跌幅超过6个点
            if dataArr[num-1]['pct_chg'] < -3:
                continue
            if num-2 < 0:
                print('数据有问题')
            # 找当天涨停，前十天未涨停的股
            datas = dataArr[num+1:num+1+10]
            for i in range(len(datas)):
                data = datas[i]
                if data['pct_chg'] > 9.7:
                    break
                if i == len(datas) - 1:
                    limitUpCodes.append([code, dataArr[num-1]['pct_chg'], dataArr[num-2]['pct_chg']])
        print('===============以下是：前十天未涨停，第一天涨停，第二天跌幅超过6个点===============')
        for item in limitUpCodes:
            print(item)
        
    # getCurrentChange(codeStr)


# 逻辑：找当天涨停，前十天未涨停的股
'''
【1】找当天涨停，前十天未涨停的股
【2】当天收盘价 * 1.02 > 最近20个交易日的最高价
【3】剔除股价高于50
【4】剔除市值低于30亿


待考虑：当天涨停的交易量要比前5天的交易量平均高、如果当天资金趋势比前几天高很多不买，千万不要买连续上涨了3天的股
'''
def getTodayZTPreNot():
    dayNum = 30
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    num = 0
    isTest = False
    if isTest:
        num = 3
    codeAndChg = {}
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        if dataArr[num]['pct_chg'] < 9.9:
            continue

        # 【2】当天收盘价 * 1.02 > 最近20个交易日的最高价
        if dataArr[num]['close'] * 1.02 < getMaxHighPrice(dataArr[num+1:num+1+20]):
            continue
        
        # 【3】剔除股价高于50
        if dataArr[num]['close'] > 50:
            continue
        if num-2 >= 0:
            codeAndChg[code] = [code, dataArr[num-1]['pct_chg'], dataArr[num-2]['pct_chg']]
        # 找当天涨停，前十天未涨停的股
        datas = dataArr[num+1:num+1+10]
        for i in range(len(datas)):
            data = datas[i]
            if data['pct_chg'] > 9.9:
                break
            if i == len(datas) - 1:
                limitUpCodes.append(code)
    print('===============以下是：找当天涨停，前十天未涨停的股===============')
    codeStr = getStrWithList(limitUpCodes[:100])
    codeAllInfo = Stoke.get_daily_basic(codeStr)
    goodCodes = []
    for key in codeAllInfo.keys():
        codeInfo = codeAllInfo[key]
        if codeInfo['total_mv'] > 400000:
            goodCodes.append(key)
    for code in goodCodes:
        if isTest:
            print(codeAndChg.get(code))
        else:
            print(code)
        
    # getCurrentChange(codeStr)

# 逻辑：追涨失败的找出几个出来
def catchUpFail():
    # 从数据最后一个开始，遍历如果连续连续3次涨停，之后连续2天下跌，记录股票代码和第二天下跌的日期
    # 连续多个封板涨停，最后破板当天交易量巨大，未涨停，未跌停，破板后一天开始下跌模式
    dayNum = 365
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]
        dataArr = dataArr.reverse()
        if len(dataArr) < dayNum:
            continue

        for i in range(len(dataArr)):
            data = dataArr[i]
            if isFengZT(data):
                if isFengZT(dataArr[i+1]):
                    limitUpCodes.append(code)
    print('===============以下是：追涨失败的找出几个出来===============')
    for code in limitUpCodes:
        print(code)

    return 0

# 逻辑：找涨幅超过8个点，(开盘价-中轨线)/中轨线<2%
def topMidZ8():
    dayNum = 20
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    index = 0
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        # if code[0:6] == '600641':
        #     print('www')
        if len(dataArr) < dayNum:
            continue

        if dataArr[index]['pct_chg'] < 8:
            continue
        cuOpenP = dataArr[index]['open']
        midP = calMB(dataArr)
        if calChange(midP, cuOpenP) < 0.02:
            limitUpCodes.append(code)
    print('===============以下是：找涨幅超过8个点，(开盘价-中轨线)/中轨线<2%===============')
    for code in limitUpCodes:
        print(code)

# 逻辑：打印当天股票的涨跌情况
# def printTodayChange(codes):
#     codeStr = ''
#     for code in codes:

'''
2.1 涨停价	只要破板了100%能买到
2.2 涨停价的95% 拍脑袋想的，不过这个数据可以回归看一下，应该有一个准确值
此处会给出下单的价格。并且需要颗粒度比较细的数据

Ps: 回归时候要判断当天是否可以进到货，其中逻辑是这样的：根据当天的成交均价是否等于涨停价来判断
'''
# def buy_suc():
#     buy_items = ['code', 'trade_data', 'listIndex']
#     buySucList = []
#     for item in buy_items:
        
'''
思路：跌破中轨线，即将回弹
[1]第一天跌破中轨线，跌幅超过2个点，收盘低于中轨线
[2]第二天开盘，收盘都低于中轨线
[3]第三天涨，开低于中轨线，收盘 < 中轨线 * 1.02
[4]删除股价超过50的
'''
def getRebackCode():
    preMvoeDay = 0
    dayNum = 2+20+preMvoeDay
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    allCodes = deleteCodes(allCodes)
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        
        if (len(dataArr) == 0) | (len(dataArr) < dayNum):
            continue
        # one_mb:第一天中轨线值
        one_data = dataArr[2+preMvoeDay]
        one_datas = dataArr[2+preMvoeDay:]
        one_mb = calMB(one_datas)
        # [1]第一天跌破中轨线，跌幅超过2个点，收盘低于中轨线
        if (one_data['close'] < one_mb) & (one_data['pct_chg'] < -2):
            two_data = dataArr[1+preMvoeDay]
            two_datas = dataArr[1+preMvoeDay:-1]
            two_mb = calMB(two_datas)
            # [2]第二天开盘，收盘都低于中轨线
            if (two_data['close'] < two_mb) & (two_data['open'] < two_mb):
                three_data = dataArr[0+preMvoeDay]
                three_datas = dataArr[preMvoeDay:-2]
                three_mb = calMB(three_datas)
                # [3]第三天涨，开低于中轨线，收盘 < 中轨线 * 1.02
                if (three_data['pct_chg'] > 0) & (three_data['open'] < three_mb) & (three_data['close'] < three_mb * 1.02):
                    # [4]删除股价超过50的
                    if three_data['close'] < 50:
                        limitUpCodes.append(code)
    print('===============以下是：跌破中轨线，即将回弹===============')
    for code in limitUpCodes:
        print(code)

    # checkCodes = limitUpCodes[:99]
    # for code in checkCodes:
    #     print(code)
    # allStr = getStrWithList(checkCodes)
    # getCurrentChange(allStr)

# 逻辑：寻找未来的大牛股
'''
【1】第一天涨幅超过8个点
【2】第二天高开超过4个点，涨停
 适合：妖股盛行的时间
'''
def searchBigCow():
    dayNum = 2
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
        # 【1】第一天涨幅超过8个点
        if dataArr[1]['pct_chg'] < 8:
            continue
        # 【2】第二天高开超过4个点，涨停
        if(dataArr[0]['open'] > dataArr[1]['close'] * 1.02) & (dataArr[0]['pct_chg'] > 9.8):
            limitUpCodes.append(code)
    print('===============以下是：寻找未来的大牛股===============')
    for code in limitUpCodes:
        print(code)

'''
【1】第一天涨停
【2】第二天涨跌幅【-5～2】，且开盘>收盘 * 1.04
'''
def getOZTD():
    dayNum = 2
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
        # 【1】第一天涨停
        if dataArr[1]['pct_chg'] < 9.7:
            continue
        # 【2】第二天涨跌幅【-2～2】，且开盘>收盘 * 1.04
        if(dataArr[0]['open'] > dataArr[1]['close'] * 1.04) & (dataArr[0]['pct_chg'] > -5) & (dataArr[0]['pct_chg'] < 2):
            limitUpCodes.append(code)
    print('===============以下是：第一天涨停，第二天涨跌幅【-5～2】，且开盘>收盘 * 1.04===============')
    for code in limitUpCodes:
        print(code)

'''
【1】当天涨幅 > 3
【2】当天交易量比前三天平均交易量都高2倍
'''
def volBigZ():
    dayNum = 5
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())

    num = 1

    bZ = []
    bD = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '300') | (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
        
        if '000025' in code:
            print('222')

        # 【1】第一天跌股超过1或者，涨幅超过0.5
        # if (dataArr[num+1]['pct_chg'] > -2) & (dataArr[num+1]['pct_chg'] < 0):
        #     continue
        if (dataArr[num+1]['pct_chg']) > 3:
            continue
        
        if (dataArr[num+2]['pct_chg']) > 3:
            continue

        # 【1】当天涨幅 > 3
        if (dataArr[num]['pct_chg'] < 9) & (dataArr[num]['pct_chg'] > 2):
            continue

        # 【2】当天交易量比前三天平均交易量都高2倍
        vols = [dataArr[num+1]['vol'], dataArr[num+2]['vol'], dataArr[num+3]['vol']]
        if (dataArr[num]['vol'] > (calAverage(vols) * 2)) & (dataArr[num]['vol'] > (dataArr[num+1]['vol'] * 2)):
            limitUpCodes.append([code, dataArr[num-1]['pct_chg']])
            pct = dataArr[num-1]['pct_chg']
            if pct < -3:
                bD.append([code, pct])
            
            if pct > 3:
                bZ.append([code, pct])
    print('跌幅比例%f' % (len(bD)/len(limitUpCodes)))
    print('涨幅比例%f' % (len(bZ)/len(limitUpCodes)))
    print('===============以下是：当天交易量比前三天平均交易量都高2倍，当天涨幅>3==============')
    for code in limitUpCodes:
        print(code)

'''
思路：寻找之前大涨， 现在正在回调的股
【1】当天跌幅超过8个点
【2】前4天，至少有2天涨停
'''
def getRebackD():
    dayNum = 20
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    for j in range(10):
        limitUpCodes = []
        num = j+2
        for i in range(len(allCodes)):
            code = allCodes[i]
            if (code[0:3] == '300') | (code[0:3] == '688'):
                continue
            dataArr = allStokeDate[code]

            if len(dataArr) < dayNum:
                continue
            # 【1】当天涨幅超过8个点
            if dataArr[num]['pct_chg'] > -8:
                continue

            # 【2】前三天有一天是涨停的
            datas = dataArr[num+1:num+1+4]
            ZT_time = 0
            for i in range(len(datas)):
                data = datas[i]
                if data['pct_chg'] > 8:
                    ZT_time += 1
                if ZT_time == 2:
                    limitUpCodes.append([code, dataArr[num-1]['pct_chg'], dataArr[num-2]['pct_chg']])
                    break
        print('===============以下是：寻找之前大涨， 现在正在回调的股===============%d' % num)
        for code in limitUpCodes:
            print(code)

'''
【1】当天涨停
【2】前一天涨幅低于3个点
【3】前十天未涨停
'''
def getBZ_Pre_10():
    dayNum = 30
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())

    for j in range(10):
        num = j+2
        limitUpCodes = []
        for i in range(len(allCodes)):
            code = allCodes[i]
            if (code[0:3] == '300') | (code[0:3] == '688'):
                continue
            dataArr = allStokeDate[code]

            if len(dataArr) < dayNum:
                continue
            # 【1】当天涨幅超过9.7个点
            if dataArr[num]['pct_chg'] < 9.7:
                continue

            # 【2】前一天涨幅低于3个点
            if dataArr[num+1]['pct_chg'] > 3:
                continue
            # [-2, -1]
            if (dataArr[num-1]['close'] == 0):
                continue

            open_chg = calChange(dataArr[num]['close'], dataArr[num-1]['open']) * 100
            if (open_chg < -2) | (open_chg > -1):
                continue

            datas = dataArr[num+1:num+1+10]
            for i in range(len(datas)):
                data = datas[i]
                if data['pct_chg'] > 9:
                    break
                if i == len(datas) - 1:
                    limitUpCodes.append([code, dataArr[num-1]['pct_chg'], dataArr[num-2]['pct_chg']])
        print('===============以下是：当天涨停，前十天未涨停===============%d' % num)
        for code in limitUpCodes:
            print(code)

'''
【1】第一天涨停
【2】第二天的开盘跌幅取[-3, -2, -1, 0, 1, 2, 3]取其中一个区间
【3】打印出第三天的涨跌比例变化
昨天涨停，今天低开的，打印第三天的股票涨跌
'''
def getDeffZD():
    dayNum = 30
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())

    for j in range(10):
        num = j+1
        min = -0.04
        print('wwwwwwwwwwwwwwww往前移%d天wwwwwwwwwwwwwww' % num)
        temp = -4
        for x in range(7):
            min += 0.01
            temp += 1
            limitUpCodes = []
            list_D = []
            list_Z = []
            for i in range(len(allCodes)):
                code = allCodes[i]
                if (code[0:3] == '300') | (code[0:3] == '688'):
                    continue
                dataArr = allStokeDate[code]

                if len(dataArr) < dayNum:
                    continue
                # 【1】第一天涨停
                if dataArr[num+1]['pct_chg'] < 9.7:
                    continue
                # 【2】第二天的开盘跌幅取[-3, -2, -1, 0, 1, 2, 3]取其中一个区间
                if (calChange(dataArr[num+1]['close'], dataArr[num]['open']) > min) & (calChange(dataArr[num+1]['close'], dataArr[num]['open']) < min + 0.01):
                    chg = dataArr[num]['pct_chg']
                    limitUpCodes.append([code, chg])
                    if chg < 0:
                        list_D.append(code)
                    elif chg > 3:
                        list_Z.append(code)
            codeStr = getStrWithList(list_Z)
            if len(limitUpCodes) > 0:
                print('第一天涨停，第二天开盘涨跌幅在(%d~%d), 第二天跌比例：%f，涨幅超过3个点比例：%f，股票代码%s' % (temp, temp+1, (len(list_D)/len(limitUpCodes)), (len(list_Z)/len(limitUpCodes)), codeStr))
            # print('===============以下是：当天涨停，前十天未涨停===============%d' % num)
            # for code in limitUpCodes:
            #     print(code)

'''
【1】第一天涨幅低于8个点
【2】第二天涨幅高于9.7个点
【3】第二天交易量比第一天高一倍以上
【4】第二天交易量要比前十天每天的交易量都高1.5以上
【5】剔除流通市值低于50亿

剔除正在下跌趋势中的票，通过前二十天到前十天的均价和前十天的均价相比 1.05
比前十天每天的交易量都高两倍

该策略：如果当天找到该票，明天如果下跌，跌破上轨线可以考虑
'''
def getNiceVol():
    dayNum = 30
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    
    isTest = False
    for j in range(10):
        num = 0
        if isTest:
            num = j+3
        limitUpCodes = []
        for i in range(len(allCodes)):
            code = allCodes[i]
            if (code[0:3] == '300') | (code[0:3] == '688'):
                continue
            dataArr = allStokeDate[code]

            if len(dataArr) < dayNum:
                continue
            # 【1】第一天涨幅低于3个点
            if dataArr[num+1]['pct_chg'] > 8:
                continue

            # 【2】第二天涨幅高于4.3个点
            if dataArr[num]['pct_chg'] < 9.7:
                continue
            
            # 【3】第二天交易量比第一天高一倍以上
            if (dataArr[num]['vol']/dataArr[num+1]['vol']) > 2:
                #【4】第二天交易量要比前十天每天的交易量都高1.5以上
                for x in range(10):
                    x = x + num+1
                    if (dataArr[x]['vol']*1.5) > dataArr[num]['vol']:
                        break
                    if x == num+10:
                        if num-3 > 0:
                            limitUpCodes.append([code, dataArr[num-1]['pct_chg'], dataArr[num-2]['pct_chg'], dataArr[num-3]['pct_chg']])
                        else:
                            limitUpCodes.append(code)
        print('===============以下是：交易量增加大涨，之后回调可能会有大涨，建议赚7个点===============%d' % num)

        newCodes = limitUpCodes[:100]
        codeStr = getStrWithList(newCodes)
        codeAllInfo = Stoke.get_daily_basic(codeStr)
        goodCodes = []
        for key in codeAllInfo.keys():
            codeInfo = codeAllInfo[key]
            if codeInfo['circ_mv'] > 500000:
                goodCodes.append(key)
        for code in goodCodes:
            print(code)
        if not isTest:
            return

'''
可以通过大单资金趋势来做T
'''

'''
当天涨幅在3-5个点，今天收盘价 * 1.1 < 前10天开盘价
'''

'''
小市值+低股价+趋势缓慢上升的
'''

'''
策略名称：找到熊牛股（250天均线，趋势向上，当股价跌到250均线附近时，同时正在放量，且站稳了止跌站稳，如果遇到趋势向下，此时逢高卖出股票）
【1】获取目前249+5个交易日的K线数据
【2】当天交易量要比前面5天都高
【3】当天收盘价要高于昨天开盘价
【4】|(当天-250均线价格)/250均线价格| < 0.1

猜测：如何提前抓到熊牛线的
【5】(当天-250均价) > -0.1 且(当天-250均价) < 0
isPre是否提前找到熊牛股
'''
def getCattleBearStoke(isPre):
    dayNum = 249+5
    #【1】获取目前249+5个交易日的K线数据
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())

    limitUpCodes = []

    # 是否需要今天涨停
    todayIsZD = True
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] == '688'):
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue
        #【2】当天交易量要比前面5天都高
        if '300456' in code:
            print('============')
        if todayIsZD:
            if dataArr[0]['pct_chg'] < 9.7:
                continue
        else:
            isBreke = False
            for num in range(5):
                if dataArr[0]['vol'] < dataArr[num+1]['vol']:
                    isBreke = True
                    break
            if isBreke:
                continue

        #【3】当天收盘价要高于昨天开盘价
        if dataArr[0]['close'] < dataArr[1]['open']:
            continue
        
        #【4】|(当天-250均线价格)/250均线价格| < 0.1
        closeArr = []
        for num in range(250):
            closeArr.append(dataArr[num]['close'])
        
        chage = calChange(calAverage(closeArr), dataArr[0]['close'])
        if abs(chage) < 0.1:
            if isPre:
                if chage < 0:
                    limitUpCodes.append([code, chage, calAverage(closeArr), dataArr[0]['close']])
            else:
                if chage > 0:
                    limitUpCodes.append([code, chage, calAverage(closeArr), dataArr[0]['close']])
        else:
            if todayIsZD:
                isNeedAdd = True
                for data in dataArr[1:5]:
                    if data['pct_chg'] > 9.7:
                        isNeedAdd = False
                if isNeedAdd:
                    limitUpCodes.append([code, chage, calAverage(closeArr), dataArr[0]['close']])
    
    print('===============以下是：找到熊牛股===============%d' % len(limitUpCodes))
    for code in limitUpCodes:
        print(code)

'''
思路：250均线附近冲高回落的，5-8周必有惊喜
【1】找最近60 + 249天的票
【2】前十天是否有出现2次涨停
【3】前十天的 每天收盘价 < 250均线价 * 1.2
【4】最近20天涨幅超过9个点的至少有3天
【】

预测未来的牛股
【1】40天内，前10天至少出现过一次大涨，每天收盘价 < 250均线 * 1.2
【2】最近5天涨幅超过9个点小于等于1天，每天收盘价 < 250均线 * 1.2
'''
def myMoney():
    dataNum = 40
    dayNum = 249+dataNum
    #【1】找最近60 + 249天的票
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    allNeedCodes = []
    
    preDay = 10
    for i in range(len(allCodes)):
        code = allCodes[i]
        if (code[0:3] != '300') :
            continue
        dataArr = allStokeDate[code]

        if len(dataArr) < dayNum:
            continue

        #【2】前二十天是否有出现2次涨停
        pre_Z_num = 0
        tempNum = dataNum-preDay-1
        # 是否已经突破了250均线，超过20个点
        isTuPo250Day = False
        for data in dataArr[dataNum-preDay:dataNum]:
            # 计算当天250均线值
            tempNum += 1
            closeArr = []
            for num in range(250):
                closeArr.append(dataArr[num+tempNum]['close'])
            chage = calChange(calAverage(closeArr), dataArr[tempNum]['close'])
            #【3】前十天的 每天收盘价 < 250均线价 * 1.2
            if chage > 0.2:
                isTuPo250Day = True
                break
            if data['pct_chg'] > 9.7:
                pre_Z_num += 1
            if pre_Z_num == 1:
                if chage > 0:
                    isTuPo250Day = True
                    break

        if isTuPo250Day:
            continue
        
        if pre_Z_num < 1:
            continue
        
        allNeedCodes.append(code)
        
        #【4】最近20天涨幅超过9个点的至少有3天
        recentZ9Num = 0
        isTuPo250Day = False
        tempNum = 0
        for data in dataArr[0:5]:
            closeArr = []
            for num in range(250):
                closeArr.append(dataArr[num+tempNum]['close'])
            chage = calChange(calAverage(closeArr), dataArr[tempNum]['close'])
            if chage > 0.2:
                isTuPo250Day = True
                break
            tempNum += 1
            if data['pct_chg'] > 9:
                recentZ9Num += 1

        if (recentZ9Num <= 1) & (not isTuPo250Day):
            limitUpCodes.append(code)

    print('5-8周内之前，250均线附近出现过小幅大涨的股票总数%d' % len(allNeedCodes))
    print('5-8周内之后，出现惊喜走势的股票总数%d' % len(limitUpCodes))

    print('===============以下是：250均线附近冲高回落的，5-8周必有惊喜===============%d' % len(limitUpCodes))
    for code in limitUpCodes:
        print(code)

'''
倒锤头+攻击性K
【1】第一天最高价 > 1.5 * abs(open - close)
【2】第二天大涨超过8个点，交易量比最近20天都高
'''

'''
找到最强股，明天开始即将大涨
【1】今天涨幅超过5个点，交易量最近20个交易日最大，收盘>开盘
【2】最近20天无涨停
【3】今天close < 250均线 * 1.3
'''
def bigBearStoke():
    numD = 1
    dayNum = 20 + 230 + 10
    #【1】找最近60 + 249天的票
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    for j in range(10):
        limitUpCodes = []
        numD = 0+j
        for i in range(len(allCodes)):
            code = allCodes[i]
            if (code[0:3] != '300') :
                continue
            
            dataArr = allStokeDate[code]
            if len(dataArr) < dayNum:
                continue
            
            #【1】今天涨幅超过5个点
            if (dataArr[numD]['pct_chg'] < 2) | (dataArr[numD]['close'] < dataArr[numD]['open']):
                continue

            #【2】最近20天无涨停，交易量最近10个交易日最大
            isZT = False
            index = 0
            for data in dataArr[numD+1:20+1]:
                if (data['pct_chg'] > 9.8):
                    isZT = True
                    break
                if index < 10:
                    index += 1
                    if (dataArr[0]['vol'] < data['vol']):
                        isZT = True
                        break
            if isZT:
                continue

            # 当天收盘价是最近50个交易日的最高价
            closeMax = getMaxInList(dataArr[numD+1:numD+50], 'close')
            if dataArr[0]['close'] < closeMax * 1.05:
                continue

                
            #【3】今天close < 250均线 * 1.3
            closeArr = []
            for num in range(250):
                closeArr.append(dataArr[num]['close'])
            chage = calChange(calAverage(closeArr), dataArr[0]['close'])
            if chage < 0.3:
                if numD == 0:
                    limitUpCodes.append(code)
                else:
                    if (numD == 1) & (dataArr[0]['pct_chg'] < -3):
                        print('Andy === %s', code)
                    limitUpCodes.append([code, dataArr[numD-1]['pct_chg']])
        print('===============往前移%d天，以下是：找到最强股，明天开始即将大涨===============%d' % (numD, len(limitUpCodes)))
        for code in limitUpCodes:
            print(code)

# 逻辑：根据list数据算出250均线价格和当前收盘价差%比 cuData：当前收盘价
def cal250PriceChage(datas, cuData):
    if len(datas) != 250:
        return 0
    closeArr = []
    for data in datas:
        closeArr.append(data['close'])
    _250Price = calAverage(closeArr)
    if _250Price == 0:
        return 0
    chage = calChange(_250Price, cuData['close'])
    return chage

# 逻辑：是否是红色倒锤头，当天涨幅超过3个点
def isRedDCT(data):
    if (data['pct_chg'] > 3):
        high_close = data['high'] - data['close']
        close_open = data['close'] - data['open']
        # eg：high:10、close:9.8、open:9.2
        if high_close > close_open * 0.3:
            return True
    return False

# 找最近5 + 249天的票
def richFunction():
    dataNum = 5
    # dayNum = 249+dataNum
    dayNum = 60
    
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    
    for i in range(len(allCodes)):
        code = allCodes[i]
        # 剔除科创板股票
        if (code[0:3] != '300') :
            del allStokeDate[code]
            continue

        # 剔除交易日还未达到要求的股票
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            del allStokeDate[code]
    # getDCTZ(allStokeDate)
    # getDP250(allStokeDate)
    get250BigZ(allStokeDate)
    # bigVolBigZ()
    
    bigVolBigZ_New()

'''
250均线附近出现放量上涨的票，需要跟进
【0】需要剔除进入下跌状态的股票、剔除最近60天内出现过3次涨停的、高位横盘太久的票千万不要买、剔除最近涨的很高的
【1】当天涨幅超过2.8个点
【2】当天的成交量 > 最近30天最高成较量 * 0.8
'''
def getDCTZ(allStokeDate):
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        # 需要剔除进入下跌状态的股票：最近20天，跌的次数比涨的次数多
        d_time = 0
        z_time = 0
        for data in dataArr[0:20]:
            if data['pct_chg'] < 0:
                d_time += 1
            elif data['pct_chg'] > 0:
                z_time += 1
        if z_time == 0:
            continue
        if (d_time / z_time) > (3/2):
            continue

        #【1】当天涨幅超过2.8个点
        if dataArr[0]['pct_chg'] < 2.8:
            continue

        #【2】当天的成交量 > 最近30天最高成较量 * 0.8
        rev_max_vol = 0
        for data in dataArr[1:31]:
            if data['vol'] > rev_max_vol:
                rev_max_vol = data['vol']
        if dataArr[0]['vol'] < rev_max_vol * 1:
            continue

        chage = cal250PriceChage(dataArr[0:250], dataArr[0])
        if abs(chage) > 0.3:
            continue

        limitUpCodes.append(code)
    print('==============250均线附近出现放量上涨的票，需要跟进:%d===============' % len(limitUpCodes))
    # for code in limitUpCodes:
    #     print(code)
    getCurrentChange(getStrWithList(limitUpCodes))
    
'''
思路：抓250均线附近出现大涨的票
【1】当天涨停，前4天abs(pct_chg) < 7
【2】abs((当天收盘价 - 250均线价) / 250均线价) < 0.2
【3】看当日分时图，是否是开盘直线涨停，是就当天追
【4】当天收盘价要高于前10-前15的平均收盘价

找到票之后再结合实盘分析：
a.日K线整体呈上涨趋势，如果是从高位跌下来的回弹涨停不考虑
b.涨停首日最好是上午10点之前就涨停
c.看日K线，前几天出现过放量上涨的形态，如果后面几天下跌是缩量下跌这股铁定得买，全仓干
'''
def get250BigZ(allStokeDate):
    allCodes = list(allStokeDate.keys())
    
    # 熊牛线附近大牛股
    limitUpCodes = []
    # 已经突破过熊牛线，目前回调波段上涨
    topUpcodes = []
    codeAndPrice = {}

    # 向前移动几天，便于测试 
    pre_move_day = 0

    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]

        # if '603976' in code:
        #     print('www')

        #【1】当天涨停，前4天abs(pct_chg) < 3
        if dataArr[pre_move_day]['pct_chg'] < 9.7:
            continue
        #【4】当天收盘价要高于前1-前11的收盘平均价

        # 前10天的收盘平均价
        close_pre_10_arr = []
        for data in dataArr[pre_move_day+1:pre_move_day+10]:
            close_pre_10_arr.append(data['close'])
        ave_close_10 = calAverage(close_pre_10_arr)
        
        if dataArr[pre_move_day]['close'] < ave_close_10:
            continue

        # if dataArr[pre_move_day]['close'] < dataArr[30+pre_move_day]['close']:
        #     continue

        if '300' in code:
            if dataArr[pre_move_day]['pct_chg'] < 19:
                continue
        pre4PctchgBig3 = False
        for data in dataArr[pre_move_day+1:pre_move_day+5]:
            if '300' in code:
                if abs(data['pct_chg']) > 14:
                    pre4PctchgBig3 = True # True
                    break
            else:
                if abs(data['pct_chg']) > 7:
                    pre4PctchgBig3 = True # True
                    break
        if pre4PctchgBig3:
            continue
        #【2】abs((当天收盘价 - 250均线价) / 250均线价) < 0.1
        # cuChage = cal250PriceChage(dataArr[pre_move_day:250+pre_move_day], dataArr[pre_move_day])
        
        # 前40-前30天，如果平均收盘价>当天收盘价：说明持股处于下跌回调
        # 前10天的收盘平均价
        close_pre_30_40_arr = []
        for data in dataArr[pre_move_day+30:pre_move_day+40]:
            close_pre_30_40_arr.append(data['close'])
        ave_close_30_40 = calAverage(close_pre_30_40_arr)
        
        if dataArr[pre_move_day]['close'] > ave_close_30_40:
            limitUpCodes.append(code)
        else:
            topUpcodes.append(code)
        codeAndPrice[code] = dataArr[pre_move_day]['close']
    print('==============抓250均线附近出现大涨的票***熊牛线附近大牛股===============')
    '''
    如果是从250均线下方开始涨停的票需要注意：
    1、先观察这只票之前上涨是否出现极速拉张，极速下跌的先例，如果以前出现过，说明这是一只垃圾票，绝对不能考虑，参考《海星股份20200922》

    如果是在250均线上方站稳了，开始涨停的票需要注意：
    1、如果市值太低的，低于50亿，只要出现了巨量换手不管当天是不是涨停，坚决卖股票，后期会暴跌，参考《湖南投资20200921》
    '''
    codeAllInfo = Stoke.get_daily_basic(getStrWithList(limitUpCodes), '20201016')
    for key in codeAllInfo.keys():
        print('%s，   简称：%s，   当前价：%0.2f，   市值（亿）：%0.2f' % (key, codeAllInfo[key]['name'], codeAndPrice[key], codeAllInfo[key]['total_mv']/10000))
    
    print('==============抓250均线附近出现大涨的票***已经突破过熊牛线，目前回调波段上涨===============')
    '''
    如果是从高位回调下来的票，当天涨停，观察MACD是什么颜色柱：
    1、如果是绿柱，明天后两天也会小跌，一旦MACD绿柱缩短或者出现缩量下跌，短期极大可能会有一个连续涨幅，参考：《正川股份20200915》
    2、如果是红柱，说明这只票明天极大可能会跌，短期难有上升空间，参考：《英特集团20200924、振德医疗20200922》
    '''
    if len(topUpcodes) != 0:
        codeAllInfo = Stoke.get_daily_basic(getStrWithList(topUpcodes))
        for key in codeAllInfo.keys():
            print('%s，   简称：%s，   当前价：%0.2f，   市值（亿）：%0.2f' % (key, codeAllInfo[key]['name'], codeAndPrice[key], codeAllInfo[key]['total_mv']/10000))

'''
思路：找最近跌破250均线，而且还出现了封板跌停的票
【1】最近5天必须出现1个封板跌停，跌幅低于9.7个点，且当天已跌破250均线
【2】最近两天必须低于250均线
'''
def getDP250(allStokeDate):
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    
    for i in range(len(allCodes)):
        code = allCodes[i]
        dataArr = allStokeDate[code]
        # 是否有大跌
        isBigDie = False
        for num in range(5):
            if dataArr[num]['pct_chg'] < -9.7:
                if (dataArr[num]['open'] == dataArr[num]['close']) & (dataArr[num]['high'] == dataArr[num]['low']):
                    isBigDie = True
                    break
        if not isBigDie:
            continue
        # 最近两天必须低于250均线
        # 当天收盘价和250均线价格的%比
        cuChage = cal250PriceChage(dataArr[0:250], dataArr[0])
        # 昨天收盘价和250均线价格的%比
        yesDayChage = cal250PriceChage(dataArr[1:251], dataArr[1])
        if (cuChage < 0) & (yesDayChage < 0):
            limitUpCodes.append(code)
    print('==============找最近跌破250均线，而且还出现了封板跌停的票===============')
    for code in limitUpCodes:
        print(code)

'''
思路：找到熊牛分界线妖股
【1】前20天-前50天有过涨停
【2】最近30天至少有20天是在熊牛分界线之下
【3】找当天成交量是否是最近20天最小的
'''
def get250YG():
    dataNum = 50
    dayNum = 249+dataNum
    
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        # 剔除科创板股票
        if (code[0:3] == '688') :
            del allStokeDate[code]
            continue

        # 剔除交易日还未达到要求的股票
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        isZT = False
        for data in dataArr[20:50]:
            if data['pct_chg'] > 9.7:
                isZT = True
                break
        if isZT == False:
            continue
        
        #【2】最近30天至少有20天是在熊牛分界线之下
        under250Time = 0
        for num in range(30):
            chage = cal250PriceChage(dataArr[num:num+250], dataArr[num])
            if chage < 0:
                under250Time += 1
            if under250Time == 20:
                break
        #【3】是否是最小成交量
        # isZXVol = True
        # # 向前移动一天
        # moveDayPre = 0
        # for data in dataArr[moveDayPre:moveDayPre+20]:
        #     if dataArr[moveDayPre]['vol'] > data['vol']:
        #         isZXVol = False
        #         break
        # if isZXVol == False:
            # continue 
        
        if under250Time >= 20:
            limitUpCodes.append(code)
    print('==============找到熊牛分界线妖股:%d===============' % len(limitUpCodes))
    # 剔除银行类、ST类、市值低于20亿
    delCode(limitUpCodes, 200000, 0)

def delCode(codes, total_mv, pe):
     # 剔除银行类、ST类、市值低
    niceCodes = []
    
    cycleTime = 1
    if (len(codes) > 100):
        cycleTime += 1
        
    codeStr = ''
    for i in range(cycleTime):
        newCodes = codes[i*100: i*100+100]
        codeStr = getStrWithList(newCodes)
        codeAllInfo = Stoke.get_daily_basic(codeStr, '20200911')

        for key in codeAllInfo.keys():
            codeInfo = codeAllInfo[key]
            if 'ST' in codeInfo['name']:
                continue
            if '银行' in codeInfo['name']:
                continue
            # 市值低于20亿
            if codeInfo['total_mv'] < total_mv:
                continue
            if codeInfo['pe'] < pe:
                continue
            niceCodes.append(key)
    print('==============剔除ST、银行、市值低于%d亿:%d===============' % (total_mv, len(niceCodes)))
    for code in niceCodes:
        print(code)

'''
思路：找刚跌到熊牛分界线附近的票
【1】最近3天有2天在熊牛分界线下方
【2】前3-前15天有8天在熊牛分界线上方
【3】最近三天abs(涨跌幅) < 2
'''
def getRecDown250K():
    dataNum = 15
    dayNum = 249+dataNum
    
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        # 剔除科创板股票
        if (code[0:3] != '300') :
            del allStokeDate[code]
            continue

        # 剔除交易日还未达到要求的股票
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        #【1】最近3天有2天在熊牛分界线下方
        is250KDownTime_0_3 = 0
        # 最近3-15天在熊牛分界线上方的次数
        is250KUpTime_3_15 = 0
        # 最近3天的涨跌幅都在2个点范围内
        isChg_2 = True
        for i in range(15):
            chage = cal250PriceChage(dataArr[i:i+250], dataArr[i])
            if i<3:
                if abs(dataArr[i]['pct_chg']) > 2:
                    isChg_2 = False
                    break
                #【3】最近三天abs(涨跌幅) < 2
                if chage < 0:
                    is250KDownTime_0_3 += 1
            else:
                if chage > 0:
                    is250KUpTime_3_15 += 1
                
        if is250KDownTime_0_3 <= 2:
            continue

        if isChg_2 == False:
            continue

        # 前3-前15天有8天在熊牛分界线上方
        if is250KUpTime_3_15 < 8:
            continue

        limitUpCodes.append(code)
    print('==============找刚跌到熊牛分界线附近的票:%d===============' % len(limitUpCodes))
    for code in limitUpCodes:
        print(code)

'''
思路：放巨量上涨，之后会有新高
【1】当日成交量是上个交易日2倍以上，最近20天成交量最好
【2】当日涨幅>3
【3】如果当天交易量比最近30天都高，这个是很好的

1、当天收盘价在最近30天最高，今天成交量比最近30天都高
2、当日成交量比最近10天都高，当天涨幅>3，最近60天内收盘价比当天高的要少于20天，低于当天收盘价的要超过35天，而且最近30天最高收盘价 < 当天收盘价*1.38

注意事项：
【1】必须满足在120或250均线附近
【2】如果当天是红色的倒锤头最好，放量很高，如果是上下影线都上的红柱，这个不好看
【3】如果最近半年已经有了两个双顶，基本不考虑，压力位太重，
'''
def bigVolBigZ():
    dayNum = 20
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '300553' in code:
            print('www')

        # 剔除非创业板股票
        if (code[0:3] != '300') :
            del allStokeDate[code]
            continue

        # 剔除交易日还未达到要求的股票
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        # 当日成交量是上个交易日2倍以上
        if dataArr[0]['vol'] < dataArr[1]['vol'] * 2:
            continue
        
        # 最近20天成交量最好
        todayVolIsBig_20 = True
        for data in dataArr[1:]:
            if dataArr[0]['vol'] < data['vol']:
                todayVolIsBig_20 = False
                break
        if todayVolIsBig_20 == False:
            continue

        # 当日涨幅>3
        if dataArr[0]['pct_chg'] < 3:
            continue
        
        limitUpCodes.append(code)            
    print('==============放巨量上涨，之后会有新高:%d===============' % len(limitUpCodes))
    for code in limitUpCodes:
        print(code)
'''
1、当天收盘价在最近10天最高，今天成交量比最近10天都高
2、当日成交量比最近10天都高，当天涨幅>3，最近60天内收盘价比当天高的要少于20天，低于当天收盘价的要超过35天，而且最近30天最高收盘价 < 当天收盘价*1.38
'''
def bigVolBigZ_New():
    # 向前偏移天数，方便测试
    pre_move = 0
    dayNum = 250+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    limitUpCodes1 = []
    limitUpCodes2 = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '300415' in code:
            print('222')
        # 剔除非创业板股票
        if (code[0:3] != '300') :
            del allStokeDate[code]
            continue

        

        # 剔除交易日还未达到要求的股票
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        # 当日涨幅低于3个点，超过15个点的剔除
        todayPct_chg = dataArr[0+pre_move]['pct_chg']
        if (todayPct_chg < 3) | (todayPct_chg > 15):
            continue

        # 当日成交量比最近10天都高
        vol_10 = True
        for data in dataArr[1+pre_move:10+pre_move]:
            if data['vol'] > dataArr[0+pre_move]['vol']:
                vol_10 = False
                break
        if vol_10 == False:
            continue
        
        # 剔除超过250均线很多的票
        # chage = cal250PriceChage(dataArr[0+pre_move:250+pre_move], dataArr[0])
        # if chage > 0.3:
        #     continue

        # 剔除当前已经涨的很多的票
        if (dataArr[0]['close'] / dataArr[60]['close']) > 1.4:
            continue

        # 最近60高于当天收盘价天数
        bigCloseNum = 0
        # 最近60低于当天收盘价天数
        lowCloseNum = 0
        # 最近30天内的最高收盘价
        max_close_30 = 0
        time = 0
        for data in dataArr[1+pre_move:60+pre_move]:
            if time < 30:
                if max_close_30 < data['close']:
                    max_close_30 = data['close']
            if data['close'] > dataArr[0+pre_move]['close']:
                bigCloseNum += 1
            elif data['close'] < dataArr[0+pre_move]['close']:
                lowCloseNum += 1
    
        # 最近60天内收盘价比当天高的要少于20天, 低于当天收盘价的要超过35天, 最近30天最高收盘价 < 当天收盘价*1.38
        if (bigCloseNum < 20) &(lowCloseNum > 35) & (max_close_30 < dataArr[0]['close'] * 1.38):
            # 剔除今天涨幅超过16个点的
            if dataArr[0]['pct_chg'] < 16:
                limitUpCodes2.append(code)

        # 当天收盘价在最近10天最高，今天成交量比最近10天都高
        tempNum = 0
        for data in dataArr[1+pre_move:10+pre_move]:
            if (dataArr[0+pre_move]['vol'] > data['vol']) &(dataArr[0+pre_move]['close'] > data['close']):
                tempNum += 1
                if tempNum == 9:
                    limitUpCodes1.append(code)        
    print('==============放巨量上涨，之后会有新高:%d===============' % len(limitUpCodes1 + limitUpCodes2))
    print('最近10天，当天收盘价和成交量都是最高')
    for code in limitUpCodes1:
        print(code)
    # getCurrentChange(getStrWithList(limitUpCodes1))
    
    print('目前处于即将大幅上涨')
    for code in limitUpCodes2:
        print(code)
    # getCurrentChange(getStrWithList(limitUpCodes2))

    

'''
思路:通过MACD指标选股，目标：【2天5个点】
【1】市值过100亿
【2】最近三天跌涨跌或者涨跌涨，要有叠加性
【3】删除远离熊牛分界线的股
【4】剔除最近3天的平均收盘价 > 最近10天的平均收盘价 * 1.2


'''        
def getMoneyWithMACD():
    dayNum = 10 + 249
    allStokeDate = getLocalKLineData(dayNum)
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        # 剔除科创板股票
        if (code[0:3] == '688') :
            del allStokeDate[code]
            continue

        # 剔除交易日还未达到要求的股票
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        if (dataArr[0]['pct_chg'] > 0) & (dataArr[1]['pct_chg'] > 0):
            continue
        
        if (dataArr[1]['pct_chg'] > 0) & (dataArr[2]['pct_chg'] > 0):
            continue
            
        if (dataArr[0]['pct_chg'] < 0) & (dataArr[1]['pct_chg'] < 0):
            continue
        
        if (dataArr[1]['pct_chg'] < 0) & (dataArr[2]['pct_chg'] < 0):
            continue
        
        ave_closes_3 = []
        for data in dataArr[0:3]:
            ave_closes_3.append(data['close'])
        ave_close_3 = calAverage(ave_closes_3)

        ave_closes_10 = []
        for data in dataArr[0:10]:
            ave_closes_10.append(data['close'])
        ave_close_10 = calAverage(ave_closes_10)

        if ave_close_3 > ave_close_10 * 1.2:
            continue
    
        chage = cal250PriceChage(dataArr[0:250], dataArr[0])
        if chage > 0.2:
            continue

        limitUpCodes.append(code)
    delCode(limitUpCodes, 1000000, 0)

'''
思路：缩量跌，止跌开始涨
'''
def stopDBeginZ():
    pre_move = 0
    dayNum = 4+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = [] 
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '300' not in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        
        if (dataArr[pre_move]['vol'] < dataArr[pre_move+1]['vol']) & (dataArr[pre_move+1]['vol'] < dataArr[pre_move+2]['vol']):
            if (dataArr[pre_move]['pct_chg'] < 0) & (dataArr[pre_move+1]['pct_chg'] < 0) & (dataArr[pre_move+2]['pct_chg'] < 0):
                limitUpCodes.append(code)
    print('==============连续三天缩量跌===============')
    for code in limitUpCodes:
        print(code)

'''
思路：在即将开始一波大涨前，提前3-5天买入
现象：前期一直低于250均线，突破250均线之后，经过30-40个交易日的回调，出现了一次放量上涨，一般3-5个工作日之后庄家开始拉升，放量涨之后几天跌的时必须买入
【1】今天放量上涨，成交量：今天 > 前一天*1.5，且比前五天都大
【2】前60-前40天，有15天低于250均线
【3】前40天-前20天，有10天以上在250均线上方，如果有超过3个涨停就剔除

买入信号：一般在出现回调的MACD指标绿柱缩短的时候就要买入
'''

'''
找市值在200亿以上，一周涨幅超过10个的，一周内未出现涨停，参考示例：首旅酒店（20201102）
'''

'''
底部横盘，连续三天主力资金净流入，参考示例：华统股份（20201113）
'''
def getLowPriceMainMoney_3():
    #获取单日全部股票数据
    niceCode = Stoke.getLowPriceMainMoney_3()
    dayNum = 60
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = []
    # 获得到连续三天资金净流入大于0的，遍历每只股，前40天-前30的平均收盘价 > 今天收盘价 * 1.2
    for code in niceCode:
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        
        # 最近10天没有涨跌幅超过8个点的
        isContinue = False
        for data in dataArr[0:10]:
            if abs(data['pct_chg']) > 7:
                isContinue = True
                break
        if isContinue:
            continue

        # 前40-前30天平均收盘价
        ave_closes_pre_30_40 = []
        for data in dataArr[30:40]:
            ave_closes_pre_30_40.append(data['close'])
        ave_close_30_40 = calAverage(ave_closes_pre_30_40)
        if ave_close_30_40 >= dataArr[0]['close'] * 1.1:
            limitUpCodes.append(code)
    print('==============底部横盘，连续三天主力资金净流入，参考示例：华统股份（20201113）===============')
    for code in limitUpCodes:
        print(code)    

# 逻辑:目前回踩boll线中轨线上涨的股很多
def getRiskWithMiddleBoll():
    pre_move = 0
    dayNum = 30+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes_10 = []
    limitUpCodes_20 = []
    # 获得当天中轨线价格
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        if '600198' in code:
            print('ww')

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        middleBollPrice = calMB(dataArr[0:20])
        # 判断当天收盘价和中轨线是否接近
        if abs(calChange(dataArr[0]['close'], middleBollPrice)) > 0.035:
            continue

        # 前面5天内有过一次大涨,涨幅超过7个点
        isExitBigZ_pre_5 = False
        for data in dataArr[1:6]:
            if data['pct_chg'] > 9:
                isExitBigZ_pre_5 = True
                break
        if not isExitBigZ_pre_5:
            continue
        
        # 前面5天收盘价必须要有2天收盘价 > 那天中轨线,且有过涨停
        bigDayNum = 0
        isExitZT_pre_5 = False
        for i in range(5):
            middleBollPrice = calMB(dataArr[i+1:i+21])
            # 判断当天收盘价和中轨线是否接近
            if dataArr[i+1]['close'] > middleBollPrice:
                bigDayNum += 1
            if dataArr[i+1]['pct_chg'] > 9.7:
                isExitZT_pre_5 = True
        if (bigDayNum > 2) & isExitZT_pre_5:
            continue
    
        print('==============上涨之后回踩boll线中轨线===============')
        for code in limitUpCodes_10:
            print(code)
        print('===创业板===')
        for code in limitUpCodes_20:
            print(code)

# 逻辑：找前几天涨停，洗盘几天再次涨停的
def getZTAgin():
    dayNum = 10
    allStokeDate = getLocalKLineData(dayNum)
    limitUpCodes = [] 
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    industryAndCode =  Stoke.getCodeInfo()
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        # 当天涨停
        if dataArr[0]['pct_chg'] < 9.7:
            continue
        
        # 前天未涨停
        if dataArr[1]['pct_chg'] > 9.7:
            continue
        
        # 最近5天是否有涨停
        isExistZD_pre5 = False
        for data in dataArr[1:5]:
            if data['pct_chg'] > 9.7:
                isExistZD_pre5 = True
                break
        
        if isExistZD_pre5 == False:
            continue

        limitUpCodes.append(industryAndCode[code]['name'])
        
    print('==============找前几天涨停，洗盘几天再次涨停的票===============')
    for name in limitUpCodes:
        print(name)

def ztfb():
    # 获得最近第一次涨停的
    # 重点关注洗1天的，第二天大跌5个点的以上的，盘中大胆买入，第三天开盘挂涨4个点卖，并设置涨幅3个点提示
    pre_move = 0
    dayNum = 10+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode =  Stoke.getCodeInfo()
    limitUpCodes = []
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if ('688' in code) | ('300' in code):
            continue
        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        # 涨停次数

        if dataArr[pre_move]['pct_chg'] < 9.7:
            continue

        isContinue = False
        for i in range(pre_move):
            if dataArr[i]['pct_chg'] > 9.7:
                isContinue = True
                break
        if isContinue == True:
            continue

        ztTime = 1
        for data in dataArr[1+pre_move:10+pre_move]:
            if data['pct_chg'] > 9.7:
                ztTime += 1
                if ztTime >= 2:
                    break
        if ztTime == 1:
            limitUpCodes.append(industryAndCode[code]['name'])
    print('==============最近%d天,%d天前首板涨停，洗盘%d天===============' % (dayNum, pre_move, pre_move))
    for name in limitUpCodes:
        print(name)
        
# 逻辑：寻找支撑线的股
'''
【1】上涨趋势中，最近10天平均价收盘价，比前30-前20天平均收盘价，高出10个点
【2】分别统计5、10、20支撑线的股
'''
def getZCXStoke():
    pre_move = 0
    dayNum = 90+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode =  Stoke.getCodeInfo()
    limitUpCodes_5 = []
    limitUpCodes_10 = []
    limitUpCodes_20 = []
    allCodes = list(allStokeDate.keys())
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        # 前30-前20天平均收盘价
        ave_price_20_30 = calDayAverage(dataArr[20:30])
        
        # 前10-当天平均收盘价
        ave_price_0_10 = calDayAverage(dataArr[:10])

        # 前100-前80天平均收盘价
        ave_price_80_90 = calDayAverage(dataArr[80:90])
        if ave_price_80_90>ave_price_0_10:
            continue

        if (ave_price_0_10/ave_price_20_30) < 1.1:
            continue
        
        ave_price_5 = calDayAverage(dataArr[:5])
        ave_price_10 = calDayAverage(dataArr[:10])
        ave_price_20 = calDayAverage(dataArr[:20])

        # 剔除ST类股票
        if 'ST' in industryAndCode[code]['name']:
            continue
        
        if '智飞生物' in industryAndCode[code]['name']:
            print('www')
        
        openPrice = dataArr[0]['open']

        # 当天开盘价低于5日、高于10日线
        if (openPrice*1.01 <= ave_price_5) & (openPrice > ave_price_10):
            limitUpCodes_5.append(industryAndCode[code]['name'])
            continue

        # 当天开盘价低于10日、高于20日线
        if (openPrice*1.01 <= ave_price_10) & (openPrice > ave_price_20):
            limitUpCodes_10.append(industryAndCode[code]['name'])
            continue
    
        # 当天开盘价低于20日
        if openPrice <= ave_price_20:
            limitUpCodes_20.append(industryAndCode[code]['name'])
        
        
        
    print('==============回调到5日均线: %d ===============' % len(limitUpCodes_5))
    for name in limitUpCodes_5:
        print(name)
    
    print('==============回调到10日均线: %d ===============' % len(limitUpCodes_10))
    for name in limitUpCodes_10:
        print(name)

    print('==============回调到20日均线: %d ===============' % len(limitUpCodes_20))
    for name in limitUpCodes_20:
        print(name)
        
# 逻辑：找出最近一直在上涨的股
def getBigStoke():
    dayNum = 200
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode = Stoke.getCodeInfo()
    allCodes = list(allStokeDate.keys())
    limitUpCodes_5 = []
    limitUpCodes_10 = []
    limitUpCodes_20 = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        num = 30
        # 10日
        intervalDay = 5

        pre_30_45 = calDayAverage(dataArr[num:num+intervalDay])
        
        num -= intervalDay
        pre_15_30 = calDayAverage(dataArr[num:num+intervalDay])
        
        num -= intervalDay
        pre_0_15 = calDayAverage(dataArr[num:num+intervalDay])

        if (pre_15_30/pre_30_45) < 1.05:
            continue
        if (pre_0_15/pre_15_30) < 1.05:
            continue


        # 找出趋势股: 最近10都在20均线上方
        
        
        # 剔除ST类股票
        if 'ST' in industryAndCode[code]['name']:
            continue

        ave_price_5 = calDayAverage(dataArr[:5])
        ave_price_10 = calDayAverage(dataArr[:10])
        ave_price_20 = calDayAverage(dataArr[:20])

        closePrice = dataArr[0]['close']

        # 当天开盘价低于5日、高于10日线
    
        if (abs(calChange(ave_price_5, closePrice)) < 0.02) & (closePrice > ave_price_10) & (ave_price_10 > ave_price_20):
            limitUpCodes_5.append(industryAndCode[code]['name'])
            continue
        
        # 当天开盘价低于10日、高于20日线
        if (abs(calChange(ave_price_10, closePrice)) < 0.02) & (closePrice > ave_price_20):
            limitUpCodes_10.append(industryAndCode[code]['name'])
            continue
        
        # 当天开盘价低于20日
        if abs(calChange(ave_price_20, closePrice)) < 0.02:
            limitUpCodes_20.append(industryAndCode[code]['name'])

        # limitUpCodes.append(industryAndCode[code]['name'])
    # print('==============找出最近一直在上涨的股：%d===============' % len(limitUpCodes))
    # for name in limitUpCodes:
    #     print(name)

    print('==============回调到5日均线: %d ===============' % len(limitUpCodes_5))
    for name in limitUpCodes_5:
        print(name)
    
    print('==============回调到10日均线: %d ===============' % len(limitUpCodes_10))
    for name in limitUpCodes_10:
        print(name)

    print('==============回调到20日均线: %d ===============' % len(limitUpCodes_20))
    for name in limitUpCodes_20:
        print(name)
        
# 逻辑：找出从250均线附近开始上涨的票，未来可以翻倍
'''
条件：
【1】当天涨停
【2】涨停当天开盘价-250均线股/250均线股 < 0.1
【3】删除从高出跌下来的股
'''
def getDoubleStoke_strong():
    pre_move = 0
    dayNum = 250+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode = Stoke.getCodeInfo()
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        
        if '000570' in code:
            print('www')

        if dataArr[0+pre_move]['pct_chg'] < 9.7:
            continue

        # 最近100天的最高价
        maxPrice_100 = getMaxClosePrice(dataArr[pre_move:100+pre_move])
        if (maxPrice_100 / dataArr[0+pre_move]['open']) > 1.25:
            continue
        
        # 最近3天，有过3次涨停，就剔除改股
        if (dataArr[pre_move]['pct_chg'] > 9.7) & (dataArr[pre_move+1]['pct_chg'] > 9.7) & (dataArr[pre_move+2]['pct_chg'] > 9.7):
            continue
        
        # 剔除最近60天中，每天收盘价都高于250均线的股
        isExitscloseLow250Day = False
        for i in range(60):
            if dataArr[i+pre_move]['close'] < calDayAverage(dataArr[i+pre_move:i+pre_move+250]):
                # print(dataArr[i+pre_move]['trade_date'])
                isExitscloseLow250Day = True
                break
        if isExitscloseLow250Day == False:
            continue


        chage = cal250PriceChage(dataArr[0+pre_move:250+pre_move], dataArr[0+pre_move])
        if (chage < 0.35) & (chage > -0.05):
            limitUpCodes.append(industryAndCode[code]['name'])
    print('==============找出从250均线附近涨停，未来可以翻倍：%d ===============' % len(limitUpCodes))
    for name in limitUpCodes:
        print(name)

# 逻辑：找出从250均线附近开始上涨的票，未来2周可以50个点
'''
条件：
【1】当天涨幅3
【2】涨停当天收盘价-250均线股/250均线股 < 0.25
【3】最近90天最高价
'''
def getDoubleStoke():
    pre_move = 0
    dayNum = 250+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode = Stoke.getCodeInfo()
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        
        if dataArr[0+pre_move]['pct_chg'] < 3:
            continue

        if '600362' in code:
            print('www')

        # 最近90天的最高价
        maxPrice_90 = getMaxClosePrice(dataArr[pre_move+1:90+pre_move])
        if (maxPrice_90 > dataArr[0+pre_move]['close']):
            continue
        
        chage = cal250PriceChage(dataArr[0+pre_move:250+pre_move], dataArr[0+pre_move])
        if (chage < 0.25) & (chage > -0.05):
            limitUpCodes.append(industryAndCode[code]['name'])
    print('==============找出从250均线附近开始上涨的票，未来2周可以50个点：%d ===============' % len(limitUpCodes))
    for name in limitUpCodes:
        print(name)
        
# 逻辑：连续上涨2天的股
def continuousZT2Day():
    pre_move = 0
    dayNum = 250+pre_move
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode = Stoke.getCodeInfo()
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue
        
        # 最近两天连续涨停
        if (dataArr[0+pre_move]['pct_chg'] < 9.7) | (dataArr[1+pre_move]['pct_chg'] < 9.7):
            continue

        if (dataArr[2+pre_move]['pct_chg'] > 9.7) | (dataArr[3+pre_move]['pct_chg'] > 9.7):
            continue

        # 最近90天的最高价
        maxPrice_90 = getMaxClosePrice(dataArr[pre_move+1:90+pre_move])
        if (maxPrice_90 > dataArr[0+pre_move]['close']):
            continue
        
        chage = cal250PriceChage(dataArr[0+pre_move:250+pre_move], dataArr[0+pre_move])
        if (chage < 0.25) & (chage > -0.05):
            limitUpCodes.append(industryAndCode[code]['name'])
    print('==============连续上涨2天的股：%d ===============' % len(limitUpCodes))
    for name in limitUpCodes:
        print(name)

# 逻辑：5日线策略
def volKLine(volType=5):
    pre_move = 0
    dayNum = volType*2 + pre_move
    allStokeDate = getLocalKLineData(dayNum)
    industryAndCode = Stoke.getCodeInfo()
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '688' in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < dayNum:
            continue

        if industryAndCode.get(code) == None:
            continue

        codeName = industryAndCode[code]['name']
        if 'ST' in codeName:
            continue
        
        # 最近5天收盘价都未跌破当日均线
        isDiePo_5 = False
        for i in range(5):
            if dataArr[pre_move+i]['close']*1.02 < calDayAverage(dataArr[pre_move+i:pre_move+i+5]):
                isDiePo_5 = True
                break
        if isDiePo_5 == True:
            # 跌破了5日线
            continue

        # 最近5天是否选在一天涨幅超过5个点的
        isExitsZ_5 = False
        # 最近5天内跌的次数
        dieDayNum = 0
        # 最近5天是否存在一天跌幅超过5个点的
        isExitsD_5 = False

        for data in dataArr[pre_move:pre_move+5]:
            if data['pct_chg'] <= -5:
                isExitsD_5 = True
                break
            if data['pct_chg'] >= 5:
                isExitsZ_5 = True
            
            if data['pct_chg'] < 0:
                dieDayNum += 1
        
        # 剔除5天内存在下跌5个点的股
        if isExitsD_5 == True:
            continue

        # 剔除5天内，不存在涨幅在5个点以上的股
        if isExitsZ_5 == False:
            continue

        # 剔除5天内下跌超过3天的
        if dieDayNum >= 3:
            continue
        
        limitUpCodes.append(codeName)
    print('==============5日线策略：%d ===============' % len(limitUpCodes))
    for name in limitUpCodes:
        print(name)

if __name__ == "__main__":
    # codes = '000407.SZ,002836.SZ,600982.SH,300117.SZ,300147.SZ,300335.SZ,300402.SZ,300519.SZ'
    # codes = '000517.SZ,000570.SZ,000659.SZ,000711.SZ,000796.SZ,000898.SZ,000955.SZ,000990.SZ,002098.SZ,002100.SZ,002103.SZ,002217.SZ,002274.SZ,002277.SZ,002342.SZ,002343.SZ,002374.SZ,002423.SZ,002470.SZ,002476.SZ,002492.SZ,002559.SZ,002591.SZ,002671.SZ,002694.SZ,002889.SZ,002903.SZ,002988.SZ,300025.SZ,300043.SZ,300048.SZ,300055.SZ,300062.SZ,300070.SZ,300173.SZ,300240.SZ,300272.SZ,300296.SZ,300303.SZ,300325.SZ,300350.SZ,300389.SZ,300647.SZ,300713.SZ,300819.SZ,300824.SZ,600027.SH,600110.SH,600116.SH,600125.SH,600159.SH,600269.SH,600287.SH,600382.SH,600540.SH,600576.SH,600642.SH,600692.SH,600707.SH,600715.SH,600757.SH,600780.SH,600792.SH,600794.SH,600796.SH,600869.SH,601008.SH,601368.SH,601588.SH,601700.SH,601869.SH,601992.SH,603012.SH,603315.SH,603356.SH,603567.SH,603585.SH,603598.SH,603918.SH'
    # 获得当天的涨跌幅
    # getCurrentChange(codes)



    # getDayKLine('600051.SH', 60)
    # getZddddStoke(5)

    # getZdowwStoke(4)
    
    # for i in range(5):
    #     getZzwStoke(3+i)

    # ZDN(False, 4)

    # ZwwdT(5)
    # for i in range(5):
    #     ZZDD(i+5)

    # recentTwoDayD(2)
    # getRecentNoBigVolBidDie(2)


    # zDVollow(2)
    # dDVollow(2)
    # recentTwoDayZOneD(3)

    
    # ZTTwo(5)

    # getTwoDayZT()

    # getTodayZTPreNot()

    # 每日必跑
    # getVolIncrease(4)
    # getRebackCode()
    # topMidZ8()
    # ZwZ()
    # getRecentlimitup(2)
    # searchBigCow()
    # getZTwoDie()
    # getTodayZTPreNot()
    # getOZTD()
    # volBigZ()
    # getBZ_Pre_10()
    # getDeffZD()
    # getRebackD()
    # getNiceVol()
    # limitupFB(1)
    # getRecentlimitup(2)

    # getCattleBearStoke(True)
    
    # myMoney()
    # bigBearStoke()
    # get250YG()

    # stopDBeginZ()
    # richFunction()
    # getRiskWithMiddleBoll()

    # getRecDown250K()
    # bigVolBigZ()
    # getMoneyWithMACD()

    # print('\n===============下面是宝的策略所选股票===============\n')
    # dZTopLBottomS()
    # lowMTopM(2)
    # print('===============憨宝的策略===============')
    # calMbUpDn()
    
    # getLowPriceMainMoney_3()

    # getZTAgin()
    # ztfb()
    # getBigStoke()
    # getZCXStoke()

    # getDoubleStoke()
    # getDoubleStoke_strong()
    # continuousZT2Day()
    volKLine()
    '''
    # 测试：用于寻找股票
    allStokeDate = getLocalKLineData(30)
    limitUpCodes = [] 
    allCodes = list(allStokeDate.keys())
    limitUpCodes = []
    
    for i in range(len(allCodes)):
        code = allCodes[i]
        if '300' not in code:
            continue

        dataArr = allStokeDate[code]
        if len(dataArr) < 10:
            print(code)
    # print('==============找最近跌破250均线，而且还出现了封板跌停的票===============')
    # for code in limitUpCodes:
    #     print(code)
    '''