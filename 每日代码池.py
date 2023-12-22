import tushare as tu
import time
import datetime
import platform
import sys, os

token = '47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899' # 阿文的token
tu.set_token(token)
pro = tu.pro_api()

globalSys_Mac = platform.system().lower() == 'darwin'
print('当前操作系统:%s' % platform.system().lower())


# 当前日期的 Unix 时间
g_currentDateUnix = 0
g_currentDate = ''

# 逻辑：路径转换
def pathToSys(path):
    if globalSys_Mac:
        return path
    else:
        return path.replace('/', '\\')
    
globalPath = pathToSys(os.getcwd() + '/')
if not globalSys_Mac:
    globalPath = 'C:\\Users\\Administrator\\Desktop\\股票数据\\'

# 获得前一天的时间
def getPreDateAndUnixTime(dateUnixTime):
    currentUnixTime = dateUnixTime - 60 * 60 * 24 * 1
    return [unixTime2LocalDate(currentUnixTime, "%Y%m%d"), currentUnixTime]

# 获得后一天的时间
def getBackDateAndUnixTime(dateUnixTime):
    currentUnixTime = dateUnixTime + 60 * 60 * 24 * 1
    return [unixTime2LocalDate(currentUnixTime, "%Y%m%d"), currentUnixTime]

# date字符串转Unix时间
def date2UnixTime(dt, format="%Y%m%d"):
    #转换成时间数组 %Y-%m-%d %H:%M:%S
    timeArray = time.strptime(dt, format)
    #转换成时间戳
    timestamp = time.mktime(timeArray)
    return timestamp

# Unix时间转date字符串
def unixTime2LocalDate(timestamp, dateFormat="%Y%m%d"):
    #转换成localtime
    time_local = time.localtime(timestamp)
    #转换成新的时间格式(2016-05-05 20:28:54)
    dt = time.strftime(dateFormat, time_local)
    return dt

def getCurrentDate(format="%Y%m%d"):
    return datetime.datetime.today().strftime(format)

def getCurrentDateUnixTime(format="%Y%m%d"):
    return date2UnixTime(getCurrentDate())

# 判断某个日期是否满一年
def beyondOneYear(date):
    global g_currentDateUnix, g_currentDate
    if g_currentDateUnix == 0:
        g_currentDate = getCurrentDate()
        g_currentDateUnix = getCurrentDateUnixTime()
    dateUnix = date2UnixTime(date)
    return g_currentDateUnix - dateUnix >= 31536000



# 当前正常上市交易的股票，指定交易所(SSE上交所 SZSE深交所)，要求上市满一年，剔除 ST 和退市
def getCurrentNormal(exchange):
    stokeCodes = []
    stokeNames = []
    stokeDates = []
    #查询当前所有正常上市交易的股票列表
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

# 获取近一个月的交易日历
def getRecentMonthTradeDate():
    curDate = getCurrentDate()
    curDateUnix = getCurrentDateUnixTime()
    # 获取近一个月的交易日历
    preMonthUnix = curDateUnix - 60*60*24*30
    preMonthDate = unixTime2LocalDate(preMonthUnix)

    datas = pro.trade_cal(exchange='', start_date=preMonthDate, end_date=curDate)
    values = datas.values
    return values

# 获取前 n 个 交易日，停牌的股票，n 默认为 5
def getSuspendedCodes(day = 5):
    origin = 5
    curDate = getCurrentDate()
    
    date = curDate
    dateUnix = date2UnixTime(date)
    
    codes = []
    while(day):
        datas = pro.query('suspend', ts_code='', suspend_date=date, resume_date='', fields='')
        if len(datas.values) != 0:
            for data in datas.values:
                code = data[0]
                if code not in codes:
                    codes.append(code)
            day -= 1
        dateUnix = getPreDateAndUnixTime(dateUnix)[1]
        date = unixTime2LocalDate(dateUnix)
    print('前%d 个交易日，发生过停牌的有'% origin, codes)
    return codes

# 是否触及涨停
def isZhang(code, tradeDate, high, preClose):
    chage = (high-preClose)/preClose
    if (('30' in code[:2]) | ('688' in code[0:3])):
        if chage > 0.198:
            print('出现了涨停，代码是:%s, 涨幅:%f, 日期是:%s' % (code, chage, tradeDate))
            return True
        return False
    else:
        if chage > 0.098:
            print('出现了涨停，代码是:%s, 涨幅:%f, 日期是:%s' % (code, chage, tradeDate))
    return chage > 0.098

# 逻辑：把数组里面的数据组成字符串
def getStrWithList(list):
    str = ''
    for code in list:
        if len(str) == 0:
            str = code
        else:
            str += ',' + code
    return str

# 获取最近几天的日 K 数据
def getDaykLine(day):
    origin = day
    curDate = getCurrentDate()
    
    date = curDate
    dateUnix = date2UnixTime(date)
    allCodeInfos = {}
    while(day):
        datas = pro.daily(trade_date=date, fields='ts_code, trade_date, high, pre_close')
        if len(datas.values) != 0:
            for data in datas.values:
                code = data[0]
                codeInfos = allCodeInfos.get(code, [])
                codeInfos.append(data)
                allCodeInfos[code] = codeInfos
            day -= 1
        dateUnix = getPreDateAndUnixTime(dateUnix)[1]
        date = unixTime2LocalDate(dateUnix)
    print('最近%d天 日K 数据获取完成' % origin)
    return allCodeInfos
    
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

# 剔除触及涨停的股
def removeTouchZhang(allCodeInfos, codes):
    answer = []
    for code in codes:
        canAdd = True
        for codeInfo in allCodeInfos[code]:
            code = codeInfo[0]
            trade_date = codeInfo[1]
            high = codeInfo[2]
            pre_close = codeInfo[3]
            if isZhang(code, trade_date, high, pre_close):
                canAdd = False
                break
        if canAdd:
            answer.append(code)
    return answer

if __name__ == "__main__":
    # 获取上交所
    codes_sh = getCurrentNormal('SSE')
    codes_sz = getCurrentNormal('SZSE')

    # 移除最近 5 日停盘的股
    codes = getSuspendedCodes()
    for susCode in codes:
        if susCode in codes_sh:
            codes_sh.remove(susCode)
        
        if susCode in codes_sz:
            codes_sz.remove(susCode)

    allCodeInfos = getDaykLine(5)
    # 获取最近 5 天的日 K 数据
    answer_sh = removeTouchZhang(allCodeInfos, codes_sh)
    answer_sz = removeTouchZhang(allCodeInfos, codes_sz)
    
    writeCodesToLocalExcel(answer_sh, False)
    writeCodesToLocalExcel(answer_sz, True)
    print('每日代码池更新完成')