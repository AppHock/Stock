import os
import tushare as tu
import 更新tushare数据
import time
import datetime
from collections import defaultdict

token = '47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899'
tu.set_token(token)
pro = tu.pro_api()

g_上市满2年_codes = []
g_市值200亿以上_codes = []

g_currentFileDir = os.path.dirname(os.path.abspath(__file__))

g_股票名_list = pro.stock_basic(list_status='L, D, P', fields='symbol, name').values.tolist()

def 递归读取所有文件路径(path):
    filesPath = []
    for root, dirs, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            filesPath.append(filepath)
    return filesPath

def 本地文件获取交易日历(s_date, e_date):
    v = 递归读取所有文件路径('/Users/hock/Stock/日K数据')
    aa = []
    for a in v:
        n = os.path.basename(a)
        d = n[:8]
        if int(d) < int(s_date) or int(d) > int(e_date):
            continue

        aa.append(n[:8])
    aa.sort()
    return aa

def 获取交易日历(s_date, e_date):
    df = pro.trade_cal(exchange='', start_date=s_date, end_date=e_date)
    交易列表 = []
    for d in list(df.values):
        if d[2] == 1:
            交易列表.append(d[1])
    return 交易列表

def 上市满2年():
    global g_上市满2年_codes
    if len(g_上市满2年_codes) != 0:
        return g_上市满2年_codes
    today = datetime.date.today()
    日期 = today.strftime('%Y%m%d')
    日期 = '20240823'
    codes = []
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    for d in data.values.tolist():
        if int(d[5]) >= 20230101:
            continue
        codes.append(d[0])
    g_上市满2年_codes = codes
    return codes

def 获取市值200亿以上(eDate, 流通市值 = 150):
    global g_市值200亿以上_codes
    if len(g_市值200亿以上_codes) != 0:
        return g_市值200亿以上_codes
    codes = []
    df = pro.daily_basic(ts_code='', trade_date=eDate, fields='ts_code,total_mv,circ_mv')
    for d in df.values.tolist():
        if d[2]/10000 <= 流通市值:
            continue
        codes.append(d[0])
    g_市值200亿以上_codes = codes
    return codes

def 趋势图形(code, 交易日历, tushare_map, 名称_map, 第一段, 第二段, 第三段, 鹏鹏版本 = False):
    price_第一段_Min = 5000
    price_第一段_Max = 0
    price_第二段_Max = 0
    price_第三段_Min = 5000
    price_第三段_Max = 0

    for 日期 in 交易日历:
        idx = 交易日历.index(日期)
        if code not in tushare_map['日K数据'][日期]:
            continue
        收盘价 = float(tushare_map['日K数据'][日期][code][3])
   
        if idx <= 第一段 - 1:
            price_第一段_Min = min(price_第一段_Min, 收盘价)
            price_第一段_Max = max(price_第一段_Max, 收盘价)
        elif idx <= 第一段 + 第二段 - 1:
            price_第二段_Max = max(price_第二段_Max, 收盘价)
        else:
            price_第三段_Min = min(price_第三段_Min, 收盘价)
            price_第三段_Max = max(price_第三段_Max, 收盘价)
        if idx > 第一段 + 第二段 + 第三段:
            break
    
    if price_第二段_Max < price_第三段_Max:
        # 剔除第二个时间段，未创新高的
        return [False, 0, 0]
    
    if price_第一段_Max > price_第二段_Max:
        # 剔除第一个时间段创新高的票（目的当前正在回调状态），可能会剔除强势股
        return [False, 0, 0]
    
    最高涨幅 = 0
    最低跌幅 = 0
    
    # 涨幅低于30个点
    if 鹏鹏版本:
        if price_第二段_Max/price_第三段_Min - 1 < 0.3:
            return [False, 0, 0]
    
        if price_第一段_Min/price_第二段_Max - 1 > -0.1:
            return [False, 0, 0]
    else:
        最高涨幅 = price_第二段_Max/price_第三段_Min - 1
        if 最高涨幅 < 0.2:
            # 剔除 第二段最高收盘价 低于 第三段 最低收盘价 20个点以上（目的剔除涨幅较弱的票）
            return [False, 0, 0]
        
        if price_第一段_Min/price_第二段_Max - 1 > -0.03:
            # 剔除 第一个时间段跌幅低于3个点（目的当前正在回调状态），可能会剔除掉强势股
            return [False, 0, 0]
        
        最低跌幅 = price_第一段_Min/price_第二段_Max - 1
        if 最低跌幅 <= -0.50:
            # 剔除 第一个时间段跌幅超过15个点（目的不能把趋势都跌破了）
            return [False, 0, 0]
        
        目前最高涨幅 = price_第一段_Max/price_第三段_Min - 1
        if 目前最高涨幅 > 0.5:
            # 短时间内已经涨幅很高了
            print(f' {名称_map[code]} 短时间涨幅{目前最高涨幅*100}%')

    return [True, 最高涨幅, 最低跌幅]

def 获取200亿股():
    codes = []
    with open('/Users/hock/Stock/股票代码.csv', 'r') as f:
        lines = f.readlines()
        for line in lines:
            codes.append(line.replace('\n', ''))
        return codes
    
def 获取上市满2年且流通市值高于(eDate, 流动市值):
    codes1 = 获取市值200亿以上(eDate, 流动市值)
    codes2 = 上市满2年()
    codes = []
    for code in codes1:
        if code in codes2:
            codes.append(code[:6])
    return codes

def 输出每日代码池(sData, eDate, 全量日期, tushare_map):  
    名称_map = {}
    for v in g_股票名_list:
        名称_map[v[0]] = v[1]

    交易日期 = 获取交易日历(sData, eDate)

    codes1 = 获取市值200亿以上(交易日期[0])
    codes2 = 上市满2年()
    codes = []
    for code in codes1:
        if code in codes2:
            codes.append(code)

    每日_map = defaultdict(list)
    
    第1段日期 = 3
    第2段日期 = 5
    第3段日期 = 20
    最短日期 = 第1段日期 + 第2段日期 + 第3段日期
    if len(tushare_map['日K数据']) < 最短日期:
        print(f'{sData} - {eDate} 只有 {len(交易日期)} 交易日， 低于数据回测所需最短交易日{最短日期}')
        return
    needCodes = []
    for code in codes:
        code = code[:6]
        # if code != '000997': continue
        # if 趋势图形(code, 交易日期, tushare_map, 名称_map, 5, 10, 45, False):
        v = 趋势图形(code, 日期, 交易日期, tushare_map, 名称_map, 3, 5, 20, False) 
        最高涨幅 = round(v[1], 4)
        最低跌幅 = round(v[2], 4)
        if v[0] == False:
            continue
        needCodes.append(code)
        名称 = 名称_map[code]
        if 'ST' in 名称:
            continue
        最新收盘价 = 0
        最新涨跌幅 = '停牌了'
        if code not in tushare_map['日K数据'][eDate]:
            continue
        c_idx = 全量日期.index(eDate)
        截止日期 = 全量日期[-1]
        if c_idx + 40 < len(全量日期):
            截止日期 = 全量日期[c_idx + 40]
        if code in tushare_map['日K数据'][截止日期]:
            最新收盘价 = float(tushare_map['日K数据'][截止日期][code][3])
            当日收盘价 = float(tushare_map['日K数据'][eDate][code][3])
            最新涨跌幅 = round(最新收盘价/当日收盘价 - 1, 4)
        
        每日_map[code] = [名称, 最高涨幅, 最低跌幅, 最新涨跌幅]

    names = []
    for code in needCodes:
        名称 = 名称_map[code]
        names.append(名称)
    print('\n')
    print('---%s 结果 %d个---' % (eDate, len(names)))
    print(names)

    if len(每日_map) == 0:
        return names
    文件夹路径 = f'{g_currentFileDir}/趋势/'
    if not os.path.exists(文件夹路径):
        os.makedirs(文件夹路径)
    文件路径 = f'{g_currentFileDir}/汇总.csv'

    模式 = 'w'
    if os.path.exists(文件路径):
        模式 = 'a'
    
    with open(文件路径, 模式) as f:
        if 模式 == 'w':
            f.write('日期,代码,名称,最高涨幅,最低跌幅,至今涨跌幅' + '\n')
        for code in 每日_map:
            v = [eDate, code]
            aa = 每日_map[code]
            for a in aa:
                v.append(str(a)) 
            f.write(','.join(v) + '\n')

    return names

def 获取最近n个交易日(n):
    eDate = datetime.datetime.now().strftime("%Y%m%d")
    交易日期 = 获取交易日历(g_sDate, eDate)
    return 交易日期[:n]

def 今日涨且为10日最高价(tushare_map, 指定日期 = ''):
    eDate = datetime.datetime.now().strftime("%Y%m%d")
    实际日期 = 获取交易日历(g_sDate, eDate)
    eDate = '20240702'
    if 指定日期 != '':
        eDate = 指定日期
    交易日期 = 获取交易日历(g_sDate, eDate)
    if len(交易日期) < 10:
        print('交易日期没有10天')
    codes = 获取上市满2年且流通市值高于(eDate, 200)

    n_codes = []
    for code in codes:
        is_code_stop = False
        今日涨跌幅 = 0
        今日收盘价 = 0
        收盘价_min = 3000
        for 日期 in 交易日期[:20]:
            收盘价 = float(tushare_map['日K数据'][日期][code][3])
            昨收价 = float(tushare_map['日K数据'][日期][code][4])
            收盘价_min = min(收盘价_min, 收盘价)
            if 日期 == 交易日期[0]:
                今日涨跌幅 = 收盘价/昨收价 - 1
                今日收盘价 = 收盘价
                # 剔除 今日涨幅低于2.5个点
                if 今日涨跌幅 < 0.025:
                    is_code_stop = True
                    break
            else:
                if 交易日期.index(日期) <= 9:
                    if 今日收盘价 < 收盘价:
                        is_code_stop = True
                        break
                    # if 日期 == 交易日期[:10][-1]:
                    #     # 近10天涨幅太高了
                    #     if 今日收盘价/收盘价 > 1.2:
                    #         is_code_stop = True
        if 今日收盘价/收盘价_min > 1.1:
            continue
        if is_code_stop:
            continue
        n_codes.append(code)
    return n_codes
    
def 打印代码名称(codes, eDate):
    names = []
    for d in g_股票名_list:
        if d[0] in codes:
            names.append(d[1])
    print('\n')
    print('---%s 结果 %d个---' % (eDate, len(names)))
    print(names)

# 603658
if __name__ == "__main__":
    eDate = datetime.datetime.now().strftime("%Y%m%d")

    sDate = '20240601'
    eDate = '20250406'
    # eDate = '20241006'
    交易日期 = 获取交易日历(sDate, eDate)
    交易日期.sort()
    for 日期 in 交易日期:
        日K文件夹路径 = '/Users/hock/Stock/日K数据/'
        日K文件路径 = os.path.join(日K文件夹路径, 日期 + '.csv')
        if not os.path.exists(日K文件路径):
            更新tushare数据.下载tushare数据(日期, 日期)
    tushare_map = 更新tushare数据.读取tushare本地缓存(日K=True,sDate=int(sDate),eDate=int(eDate))

    # for 日期 in ['20240506', '20240531', '20240617', '20240705', '20240729']:
    #     codes = 今日涨且为10日最高价(tushare_map, 日期)
    #     打印代码名称(codes, 日期)
    最新日期 = 交易日期[-1]
    for date in 交易日期:
        if int(date) < 20240730:
            continue
        输出每日代码池(sDate, date, 交易日期, tushare_map)
    