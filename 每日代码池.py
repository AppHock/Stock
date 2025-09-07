import tushare as tu
import time
import datetime

token = '47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899' # 阿文的token
tu.set_token(token)
pro = tu.pro_api()

# 当前日期的 Unix 时间
g_currentDateUnix = 0
g_currentDate = ''

# date字符串转Unix时间
def date2UnixTime(dt):
    #转换成时间数组 %Y-%m-%d %H:%M:%S
    timeArray = time.strptime(dt, "%Y%m%d")
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

def getCurrentDateUnixTime(format="%Y%m%d"):
    return datetime.datetime.today().strftime(format)

# 判断某个日期是否满一年
def beyondOneYear(date):
    global g_currentDateUnix, g_currentDate
    if g_currentDateUnix == 0:
        curDate = getCurrentDateUnixTime()
        g_currentDate = curDate
        curDateUnix = date2UnixTime(curDate)
        g_currentDateUnix = curDateUnix
    dateUnix = date2UnixTime(date)
    return g_currentDateUnix - dateUnix >= 31536000



# 当前正常上市交易的股票，指定交易所(SSE上交所 SZSE深交所)
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

        if '20230510' == fisrtDate:
            print('ww')
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

# 前 5 日未触及涨停板和停牌

# 是否触及涨停
def isZhang(code, chage, tradeDate):
    if (('300' in code) | ('688' in code)) & (chage > 0.198):
        print('出现了涨停，代码是:%s, 涨幅:%f, 日期是:%s' % (code, chage, tradeDate))
        return True
    if chage > 0.098:
        print('出现了涨停，代码是:%s, 涨幅:%f, 日期是:%s' % (code, chage, tradeDate))
    return chage > 0.098



# 逻辑：查询某只股票最近多少天的日K数据,
def getDayKLine(codes, day):
    global g_currentDateUnix, g_currentDate
    startDate = unixTime2LocalDate(g_currentDateUnix - 60 * 60 * 24 * day, "%Y%m%d")
    datas = pro.daily(ts_code=codes, start_date=startDate, end_date=g_currentDate, fields='ts_code, trade_date, high, pre_close') # 
    # 查询某只股票最近15个交易日天内如果有跌幅超过9%，说明这只股很危险，
    highClose = 0
    todayClose = 0
    allClose = 0
    times = 0
    print('正在处理的code：%s'%codes)
    for data in datas.values:
        code = data[0]
        trade_date = data[1]
        high = data[2]
        pre_close = data[3]
        high_chg = (high-pre_close)/pre_close
        return isZhang(code, high_chg, trade_date)
    return False

# 逻辑：把数组里面的数据组成字符串
def getStrWithList(list):
    str = ''
    for code in list:
        if len(str) == 0:
            str = code
        else:
            str += ',' + code
    return str

# 通过日期获取日K 数据
def getDaykLine(date):
    df = pro.daily(trade_date='20180810')

# 获取最近几个交易日的数据
# def getRecentlyDayK(day):
    
    


if __name__ == "__main__":

    codes = getCurrentNormal('SSE')
    codes_str = getStrWithList(codes)
    answer = []
    for code in codes:
        if not getDayKLine(code,7):
            answer.append(code)
    
    print('需要创建的文件路径')