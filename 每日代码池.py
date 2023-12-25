import tushare as tu
import time
import datetime
import platform
import sys, os

token = '47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899'  # 阿文的token
tu.set_token(token)
pro = tu.pro_api()

globalSys_Mac = platform.system().lower() == 'darwin'
print('当前操作系统:%s' % platform.system().lower())

# 当前日期的 Unix 时间
g_currentDateUnix = 0
g_currentDate = ''

# 设置一个时间，用于判断是用于【当日】还是【下一个交易日】交易池
g_isPreDate = datetime.datetime.now().time().hour < 17


# 逻辑：路径转换
def pathToSys(path):
    if globalSys_Mac:
        return path
    else:
        return path.replace('/', '\\')


globalPath = pathToSys(os.getcwd() + '/')
if not globalSys_Mac:
    globalPath = 'C:\\Users\\LJR\\Desktop\\股票数据\\'

# date字符串转Unix时间
def date2UnixTime(dt, format="%Y%m%d"):
    # 转换成时间数组 %Y-%m-%d %H:%M:%S
    timeArray = time.strptime(dt, format)
    # 转换成时间戳
    timestamp = time.mktime(timeArray)
    return timestamp


# Unix时间转date字符串
def unixTime2LocalDate(timestamp, dateFormat="%Y%m%d"):
    # 转换成localtime
    time_local = time.localtime(timestamp)
    # 转换成新的时间格式(2016-05-05 20:28:54)
    dt = time.strftime(dateFormat, time_local)
    return dt


def getCurrentDate(format="%Y%m%d"):
    return datetime.datetime.today().strftime(format)


def getCurrentDateUnixTime(format="%Y%m%d"):
    return date2UnixTime(getCurrentDate())


# 判断某个日期是否满一年
def beyondOneYear(date):
    currentDate = getCurrentDate()
    return int(currentDate)-int(date) >= 10000


# 当前正常上市交易的股票，指定交易所(SSE上交所 SZSE深交所)，要求上市满一年，剔除 ST 和退市
def getCurrentNormal(exchange):
    stokeCodes = []
    stokeNames = []
    stokeDates = []
    # 查询当前所有正常上市交易的股票列表
    data = pro.stock_basic(exchange=exchange, list_status='L', fields='ts_code,symbol,name,list_date')
    for codeInfo in data.values:
        code = codeInfo[0]
        symbol = codeInfo[1]
        name = codeInfo[2]

        fisrtDate = codeInfo[3]
        # 上市未满一年
        if not beyondOneYear(fisrtDate):
            continue

        # 剔除st、退市
        if ('ST' in name) | ('退' in name):
            continue
        stokeCodes.append(code)
        stokeNames.append(name)
        stokeDates.append(fisrtDate)
    return stokeCodes


# 获取近几天交易日，返回开始和结束日期字符串
def getRecentTradeDate(day=5, hour=17):
    global g_isPreDate

    origin = day
    curDate = getCurrentDate()
    curDateUnix = getCurrentDateUnixTime()

    # 获取近一个月的交易日历
    preMonthUnix = curDateUnix - 60 * 60 * 24 * 30
    preMonthDate = unixTime2LocalDate(preMonthUnix)

    datas = pro.trade_cal(exchange='', start_date=preMonthDate, end_date=curDate)
    tradeDate = []

    preDate = g_isPreDate
    for data in datas.values:
        if data[2] == 1:
            if preDate:
                preDate = False
                continue
            tradeDate.append(data[1])
            day -= 1
            if day == 0:
                break

    print('最近%d个交易日历是' % origin, tradeDate)
    return tradeDate

# 逻辑：往本地Excel写数据
def writeCodesToLocalExcel(codes, isSZ):
    global globalPath
    suffix = "上证"
    if isSZ:
        suffix = "深证"
    saveDir = pathToSys(globalPath + '每日代码池/')
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    path = saveDir + suffix + '.csv'
    symbolFile = open(path, 'w+', encoding='utf8')
    # 写入头部名称
    symbolFile.write('股票代码\n')
    for code in codes:
        s = '%s\n' % (code)
        symbolFile.write(s)
    symbolFile.flush()
    print(suffix + '的交易数据保存 Excel 完成')

# 获取某天的日 K 数据
def getDaykLineByDate(date):
    dayKInfo = {}
    datas = pro.daily(trade_date=date, fields='ts_code, trade_date, high, pre_close')
    for data in datas.values:
        dayKInfo[data[0]] = data
    return dayKInfo


# 获取某天全部股票数据涨跌停价格
def getStkLimitByDate(date):
    datas = pro.stk_limit(trade_date=date)
    stkInfo = {}
    for data in datas.values:
        stkInfo[data[1]] = data
    return stkInfo


# 获取某天的停盘数据
def getSuspendedCodesByDate(date):
    datas = pro.query('suspend', ts_code='', suspend_date=date, resume_date='', fields='')
    subpendedCodes = []
    for data in datas.values:
        subpendedCodes.append(data[0])
    return subpendedCodes


if __name__ == "__main__":
    # 获取最近5个交易日
    tradeDate = getRecentTradeDate()
    # 获取上交所和深交所
    codes_sh = getCurrentNormal('SSE')
    codes_sz = getCurrentNormal('SZSE')

    # 遍历最近5个交易日期
    for date in tradeDate:
        # 获取某天的停盘数据，并剔除该天停盘的股票
        subpendedCodes = getSuspendedCodesByDate(date)
        for susCode in subpendedCodes:
            if susCode in codes_sh:
                codes_sh.remove(susCode)

            if susCode in codes_sz:
                codes_sz.remove(susCode)

        # 获取某天的日K数据
        dayKInfo = getDaykLineByDate(date)
        if (g_isPreDate == False) & (date == tradeDate[0]) & (len(dayKInfo.values()) == 0):
            # 如果交易日下午 5 点以后，tushare 还未提供日 K 数据，则需要报错提示
            print('发生了严重问题，tushare 在 %s 日的下午 5 点以后，还未提供日 K 数据' % date)
            sys.exit(1)
        # 获取某天的股票涨跌停价格
        stkInfo = getStkLimitByDate(date)

        for code in codes_sh:
            # 剔除当天触摸了涨停的股
            if dayKInfo[code][2] == stkInfo[code][2]:
                print('股票：%s，在%s天，触摸了涨停价%f' % (code, date, stkInfo[code][2]))
                codes_sh.remove(code)

        for code in codes_sz:
            # 剔除当天触摸了涨停的股
            if dayKInfo[code][2] == stkInfo[code][2]:
                print('股票：%s，在%s天，触摸了涨停价%f' % (code, date, stkInfo[code][2]))
                codes_sz.remove(code)

    writeCodesToLocalExcel(codes_sh, False)
    writeCodesToLocalExcel(codes_sz, True)
    print('每日代码池更新完成')