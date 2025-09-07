import os 
import tushare as ts
from datetime import datetime  
import csv
import sys
import time
import multiprocessing
from multiprocessing import Pool, cpu_count
from pathlib import Path  
import pandas as pd
from collections import defaultdict  


current_file_path = os.path.abspath(__file__)
folder_path = os.path.dirname(current_file_path)
g_currentFileDir = os.path.dirname(os.path.abspath(__file__))

# sys.path.extend([current_file_path])

# tushare同一个token不支持多进程！！！！！！！！！！！！！！！！！！
ts.set_token('47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899')
pro = ts.pro_api()

def 获取交易日历(s_date, e_date):
    df = pro.trade_cal(exchange='', start_date=s_date, end_date=e_date)
    交易列表 = []
    for d in list(df.values):
        if d[2] == 1:
            交易列表.append(d[1])
    return 交易列表

def count_csv_lines(file_path):
  if not os.path.exists(file_path):
    return 0
  with open(file_path, 'r', encoding='utf_8_sig') as f:
    reader = csv.reader(f)
    line_count = sum(1 for row in reader)
    return line_count

def 比较两个日期间隔时间(t1, t2, margin):
  # 将字符串转换为datetime对象  
  date1 = datetime.strptime(t1, '%Y%m%d')  
  date2 = datetime.strptime(t2, '%Y%m%d')  
    
  # 计算两个日期之间的时间差，以天为单位  
  delta_days = (date2 - date1).days  
    
  # 判断时间差是否超过90天  
  return delta_days >= margin

def 更新最新的股票列表信息():
  path = '/home/andy/Damon/Strategy/数据文件/'
  if not os.path.exists(path):
    os.makedirs(path)
  文件路径 = path + '股票列表.csv'
  datas  = pro.stock_basic(list_status='L, D, P', fields='symbol, name, market, list_status, list_date')
  with open(文件路径, 'w', newline='', encoding='utf_8_sig') as f:
    writer = csv.writer(f)
    for data in datas.values:
      row = [str(item) if item is not None else 'None' for item in data]  
      writer.writerow(row)

def 下载并缓存日K数据(sDate, eDate):
  # https://www.tushare.pro/document/2?doc_id=27
  path = folder_path + '/日K数据/'
  if not os.path.exists(path):
    os.makedirs(path)
  日期列表 = 获取交易日历(sDate, eDate)
  for 日期 in 日期列表:
    文件路径 = path + 日期 + '.csv'
    with open(文件路径, 'w', newline='', encoding='utf_8_sig') as f:
      writer = csv.writer(f)
      df = pro.daily(trade_date=日期)
      writer.writerow(['代码','日期','开盘价','最高价','最低价','收盘价','前复权昨收价','成交量','成交额','全天vwap'])
      for data in df.values:
        row = [str(item) for item in data]  
        row[0] = row[0][:6]
        volume = int(float(row[9])*100)
        money = int(float(row[10])*1000)
        vwap = money/volume
        writer.writerow([row[0],row[1],row[2],row[3],row[4],row[5],row[6],volume,money,vwap])

def 下载并缓存除权除息数据(sDate, eDate):
  # https://www.tushare.pro/document/2?doc_id=103
  path =  folder_path + '/除权息/'
  if not os.path.exists(path):
    os.makedirs(path)
  日期列表 = 获取交易日历(sDate, eDate)
  for 日期 in 日期列表:
    文件路径 = path + 日期 + '.csv'
    with open(文件路径, 'w', newline='', encoding='utf_8_sig') as f:
      writer = csv.writer(f)
      writer.writerow(['代码', '日期'])
      df = pro.dividend(ex_date=日期, fields='ts_code,div_proc,stk_div,record_date,ex_date')
      for data in df.values:
        writer.writerow([data[0][:6], 日期])


# df = pro.suspend_d(suspend_type='S', trade_date='20210804')
# len(df.values)
def 下载并缓存停牌数据(sDate, eDate):
  # https://www.tushare.pro/document/2?doc_id=214
  path = folder_path + '/停牌/'
  if not os.path.exists(path):
    os.makedirs(path)
  日期列表 = 获取交易日历(sDate, eDate)
  for 日期 in 日期列表:
    文件路径 = path + 日期 + '.csv'
    with open(文件路径, 'w', newline='', encoding='utf_8_sig') as f:
      writer = csv.writer(f)
      writer.writerow(['代码', '日期'])
      df = pro.suspend_d(suspend_type='S', trade_date=日期)
      for data in df.values:
        writer.writerow([data[0][:6], 日期]) 

def 下载并缓存涨跌停数据(sDate, eDate):
    # https://www.tushare.pro/document/2?doc_id=183
    path = folder_path + '/涨跌停/'
    if not os.path.exists(path):
        os.makedirs(path)
    日期列表 = 获取交易日历(sDate, eDate)
    for 日期 in 日期列表:
        print('剩余 %d 日' % (len(日期列表) - 日期列表.index(日期) - 1))
        文件路径 = path + 日期 + '.csv'
        with open(文件路径, 'w', newline='', encoding='utf_8_sig') as f:
            writer = csv.writer(f)
            writer.writerow(['代码','日期','昨收价','涨停价','跌停价'])
            df = pro.stk_limit(trade_date=日期, fields ='trade_date,ts_code,pre_close,up_limit,down_limit')
            for data in df.values:
                row = [str(item) for item in data]  
                row[1] = row[1][:6]
                # 交换日期 与 代码的位置
                date = row[0]
                row[0] = row[1]
                row[1] = date
                writer.writerow(row)
    


# 更新最新的股票列表信息()

def 获取股票列表详细信息():
    #股票列表 提供一下字段 最新的股票名称、归属地、行业、上市时间 

    f_股票列表详细信息 = open('/root/Whale/new_mode_backtest/001_暗夜王墟/tushare缓存/股票列表.csv', 'r', encoding='utf-8-sig')
    lines = f_股票列表详细信息.readlines()
    f_股票列表详细信息.close()

    map_股票列表详细信息 = {}
    for line in lines:
        linelist = line.replace('\n','').replace('\'','').replace('[','').replace(']','').replace(' ','').split(',')
        股票代码 = linelist[1][0:6]
        最新股票名称 = linelist[2]
        归属地 = linelist[3]
        行业 = linelist[4]
        上市时间 = linelist[6]

        if (股票代码 not in map_股票列表详细信息):
            map_股票列表详细信息[股票代码] = {}
        
        map_股票列表详细信息[股票代码]["最新股票名称"] = 最新股票名称
        map_股票列表详细信息[股票代码]["归属地"] = 归属地
        map_股票列表详细信息[股票代码]["行业"] = 行业
        map_股票列表详细信息[股票代码]["上市时间"] = 上市时间
    return map_股票列表详细信息

# 获取股票列表详细信息()

def 生成股票列表():
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    df1 = data.values.tolist()

    股票列表 = []

    for item in df1:
        股票列表.append(item)
    return 股票列表

def 生成日期对应代码池(当前日期):
    pass 

def 获取日K数据(日期):
    # 涨跌停数据


    # 日K数据
    df = pro.daily(trade_date=日期)
    df1 = df.values.tolist()

    日K数据_list = []

    for item in df1:
        日K数据_list.append(item)
    return 日K数据_list


def 获取涨跌停数据(日期):
    # 涨跌停数据
    df = pro.stk_limit(trade_date=日期)
    df1 = df.values.tolist()

    涨跌停map = {}
    for item in df1:
      涨跌停map[item[1][:6]] = [item[2], item[3]]
    return 涨跌停map

def 获取除权除息数据(日期):
    df = pro.dividend(ex_date=日期, fields='ts_code,div_proc,stk_div,record_date,ex_date')
    df1 = df.values.tolist()

    result_list = []

    for item in df1:
        result_list.append(item[0][0:6])
    
    return result_list

def 获取停牌数据(日期):
    df = pro.suspend_d(suspend_type='S', trade_date=日期)
    df1 = df.values.tolist()

    result_list = []

    for item in df1:
        result_list.append(item[0][0:6])
    
    return result_list

def 获取前多少日停牌数据合集(日期列表):
    map_result = {}
    for 日期 in 日期列表:
        当天列表 = 获取停牌数据(日期)

        for symbol in 当天列表:
            map_result[symbol] = 1
    return map_result.keys()

def 获取前多少日除权除息数据合集(日期列表):
    map_result = {}
    for 日期 in 日期列表:
        当天列表 = 获取除权除息数据(日期)

        for symbol in 当天列表:
            map_result[symbol] = 1
    return map_result.keys()

def 获取前多少日触及涨跌停板(日期列表):
    map_result = {}

    for 日期 in 日期列表:
        df = pro.limit_list_d(trade_date=日期, fields='ts_code,limit')
        df1 = df.values.tolist()
    
        for item in df1:
            if (item[1] == 'U' or item[1] == 'D'):
                map_result[item[0][0:6]] = item[1] 
    
    return map_result

def 获取前多少日触及涨停板(日期列表):
    map_result = {}

    for 日期 in 日期列表:
        df = pro.limit_list_d(trade_date=日期, fields='ts_code,limit')
        df1 = df.values.tolist()
    
        for item in df1:
            if (item[1] == 'U'):# or item[1] == 'D'
                map_result[item[0][0:6]] = item[1] 
    
    return map_result

def 获取前多少日触及跌停板(日期列表):
    map_result = {}

    for 日期 in 日期列表:
        df = pro.limit_list_d(trade_date=日期, fields='ts_code,limit')
        df1 = df.values.tolist()
    
        for item in df1:
            if (item[1] == 'D'):
                map_result[item[0][0:6]] = item[1] 
    
    return map_result

def 获取股票当时名称(股票代码, 日期):
    # return ""
    if (股票代码[0] == '4' or 股票代码[0] == '8'): return "0"  
    if (int(股票代码) >= 600000):
        股票代码 = 股票代码 + ".SH"
    else:
        股票代码 = 股票代码 + ".SZ"

    df = pro.namechange(ts_code=股票代码, fields='ts_code,name,start_date,end_date,change_reason')
    df1 = df.values.tolist()

    时间段 = {}
    index = 0
    for item in df1: 
        时间段[index] = {}
        时间段[index]["起始时间"] = item[2]
        时间段[index]["结束时间"] = item[3]
        时间段[index]["股票名称"] = item[1]
        index += 1
    
    for index_t in 时间段:
        if (时间段[index_t]["结束时间"] == None):
            if (int(日期) >= int(时间段[index_t]["起始时间"])):
                return 时间段[index_t]["股票名称"]
        else:
            if (int(日期) >= int(时间段[index_t]["起始时间"]) and int(日期) <= int(时间段[index_t]["结束时间"])):
                return 时间段[index_t]["股票名称"]
    # print(时间段)

def 获取股票当时名称_自带缓存(股票代码, 日期, 缓存):
    # return ""
    时间段 = {}
    index = 0
    for item in 缓存: 
        时间段[index] = {}
        时间段[index]["起始时间"] = item[2]
        时间段[index]["结束时间"] = item[3]
        时间段[index]["股票名称"] = item[1]
        index += 1
    
    for index_t in 时间段:
        if (时间段[index_t]["结束时间"] == "None"):
            if (int(日期) >= int(时间段[index_t]["起始时间"])):
                return 时间段[index_t]["股票名称"]
        else:
            if (int(日期) >= int(时间段[index_t]["起始时间"]) and int(日期) <= int(时间段[index_t]["结束时间"])):
                return 时间段[index_t]["股票名称"]
    # print(时间段)

def 获取股票市值(当前日期):
    map_result = {}
    df = pro.query('daily_basic', ts_code='', trade_date=当前日期,fields='ts_code,total_mv')
    # df = pro.index_dailybasic(trade_date=当前日期, fields='ts_code,total_mv')
    df1 = df.values.tolist()

    for item in df1:
        map_result[item[0][0:6]] = float(item[1]) * 10000
    
    sorted_list = sorted(map_result.items(), key=lambda x: x[1], reverse=False)

    res = 获取股票列表详细信息()
    map_return = {}
    
    索引_计数 = 0
    for item in sorted_list:
        
        symbol = item[0]
        symbol_name = res[symbol]['最新股票名称']

        if ('退' in symbol_name or 'st' in symbol_name or 'St' in symbol_name or 'sT' in symbol or 'ST' in symbol):
            continue
        
        print(item[0], item[1])
        索引_计数 += 1
        if (索引_计数 == 400): break 

def 下载每日指标(date):
    文件夹路径 = '/Users/hock/Stock/每日指标'
    if not os.path.exists(文件夹路径):
        os.makedirs(文件夹路径)
    title = '股票代码,当日收盘价,换手率,量比,市盈率,市净率,市销率,股息率,总股本(万股),流通股本(万股),总市值(万元),流通市值(万元)'
    df = pro.query('daily_basic', ts_code='', trade_date=date, fields='ts_code,close,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,total_share,float_share,total_mv,circ_mv')
    datas = df.values.tolist()
    文件路径 = f'{文件夹路径}/{date}.csv'
    with open(文件路径, 'w') as f:
        f.write(title + '\n')
        for d in datas:
            d[0] = d[0][:6]
            v = [str(a) for a in d]
            l = ','.join(v)
            f.write(l + '\n')

def 读取每日指标(sDate, eDate):
    文件夹路径 = '/Users/hock/Stock/每日指标'
    日期列表 = 获取交易日历(sDate, eDate)
    for 日期 in 日期列表:
        path = f'{文件夹路径}/{日期}.csv'
        if not os.path.exists(path):
            下载每日指标(日期)
            
    files = 递归读取所有文件路径(文件夹路径)
    每日指标_map = {}
    for file in files:
        日期 = os.path.basename(file).split('.')[0]
        if int(日期) < int(sDate) or int(日期) > int(eDate):
            continue
        with open(file, 'r') as f:
            lines = f.readlines()
            title_v = lines.pop(0).replace('\n', '').split(',')
            for l in lines:
                v = l.replace('\n', '').split(',')
                代码 = v[title_v.index('股票代码')]
                总市值 = v[title_v.index('总市值(万元)')]
                流通市值 = v[title_v.index('流通市值(万元)')]
                总股本 = v[title_v.index('总股本(万股)')]
                流股本 = v[title_v.index('流通股本(万股)')]
                if 日期 not in 每日指标_map:
                    每日指标_map[日期] = {}
                每日指标_map[日期][代码] = [总市值, 流通市值, 总股本, 流股本]
    return 每日指标_map

def 删除代码():
    文件夹路径 = '/Users/hock/Stock/每日指标'
    files = 递归读取所有文件路径(文件夹路径)
    for file in files:
        lines = []
        with open(file, 'r') as f:
            lines = f.readlines()
        title = lines.pop(0)
        
        new_lines = []
        for line in lines:
            v = line.split(',')
            code = v[0][:6]
            v[0] = code
            new_lines.append(','.join(v))

        with open(file, 'w') as f:
            f.write(title)
            for l in new_lines:
                f.write(l)
        
def 获取股票名称():
    代码_名称 = {}
    股票列表 = pro.stock_basic(exchange='', list_status='L, D, P', fields='ts_code,symbol,name,area,industry,list_date')
    for d in 股票列表.values.tolist():
        代码 = d[1]
        名称 = d[2]
        上市日期 = d[5]
        代码_名称[代码] = [名称, 上市日期]
    return 代码_名称




def 获取历史指数权重股(指数名称):
    map_指数代码 = {
        "沪深300": 
        { 
            "名称": "399300.SZ",
            "成分股数量": 300
        },
        "中证500": 
        {
            "名称": "000905.SH",
            "成分股数量": 500
        },
        "中证1000": 
        {
            "名称": "000852.SH",
            "成分股数量": 1000
        },
        "中证2000": 
        {
            "名称": "932000.CSI",
            "成分股数量": 2000
        }
    }

    f_result = open('/root/Whale/new_mode_backtest/001_暗夜王墟/tushare缓存/指数成分股/历史_%s.csv'%(指数名称),'w',encoding='utf-8-sig')

    for 年度 in [2023,2024]:
        for 月份 in range(1,13):
            当前月份 = '%s%02d'%(年度, 月份)
            print(指数名称, 当前月份)

            df = pro.index_weight(index_code=map_指数代码[指数名称]["名称"], start_date='%s01'%(当前月份), end_date="%s31"%(当前月份))
            df1 = df.values.tolist()

            
            for item in df1:
                print(item, file = f_result)
    



    
g_tushare = {}

def 递归读取所有文件路径(path):
    filesPath = []
    for root, dirs, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            filesPath.append(filepath)
    return filesPath

def 读取文件夹所有csv文件(路径, sDate=20160101, eDate=20240301):
    t0 = time.time()
    files = 递归读取所有文件路径(路径)

    for file in files:
        date = int(os.path.basename(file)[:8])
        if date < sDate or date > eDate:
            continue
        with open(file, 'r') as f:
            lines = f.readlines()
            lines.pop(0)
            日期 = os.path.basename(file).split('.')[0]
            if '日K数据' in file:
                所有日Kmap = g_tushare.get('日K数据', {})
                单日KMap = 所有日Kmap.get(日期, {})
                for line in lines:
                    values = line.replace('\n', '').split(',')
                    # 代码: [开盘价, 最高价, 最低价, 收盘价, 前复权昨收价, 成交量, 成交额, 全天vwap]
                    单日KMap[values[0]] = [values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9]]
                所有日Kmap[日期] = 单日KMap
                g_tushare['日K数据'] = 所有日Kmap
            elif '涨跌停' in file:
                所有日Kmap = g_tushare.get('涨跌停', {})
                单日KMap = 所有日Kmap.get(日期, {})
                for line in lines:
                    values = line.replace('\n', '').split(',')
                    # 代码:[涨停, 跌停, 昨收价]
                    单日KMap[values[0]] = [values[3], values[4], values[2]]
                所有日Kmap[日期] = 单日KMap
                g_tushare['涨跌停'] = 所有日Kmap
            elif '除权息' in file:
                所有日Kmap = g_tushare.get('除权息', {})
                单日列表 = 所有日Kmap.get(日期, [])
                for line in lines:
                    values = line.replace('\n', '').split(',')
                    单日列表.append(values[0])
                所有日Kmap[日期] = 单日列表
                g_tushare['除权息'] = 所有日Kmap
            elif '停牌' in file:
                所有日Kmap = g_tushare.get('停牌', {})
                单日列表 = 所有日Kmap.get(日期, [])
                for line in lines:
                    values = line.replace('\n', '').split(',')
                    单日列表.append(values[0])
                所有日Kmap[日期] = 单日列表
                g_tushare['停牌'] = 所有日Kmap
    t1 = time.time()
    print('耗费[%d]秒，读完[%s]中的所有csv文件' % (t1-t0, 路径))
    return g_tushare

def 读取tushare本地缓存(日K = False, 涨跌停 = False, 除权息 = False, 停牌 = True, sDate=20160101, eDate=20240301):
    日期列表 = 获取交易日历(sDate, eDate)
    for 日期 in 日期列表:
        日K文件夹路径 = '/Users/hock/Stock/日K数据'
        日K文件路径 = os.path.join(日K文件夹路径, 日期 + '.csv')
        if not os.path.exists(日K文件路径):
            下载tushare数据(日期, 日期)

    本地tushare缓存路径 = folder_path
    # 本地tushare缓存路径 = '/home/andy/Damon/Strategy/数据文件'
    日期列表 = 获取交易日历(sDate, eDate)
    for 日期 in 日期列表:
        # 日期 = '20240926'
        日K文件夹路径 = os.path.join(本地tushare缓存路径, '日K数据')
        日K文件路径 = os.path.join(日K文件夹路径, 日期 + '.csv')
        if not os.path.exists(日K文件路径):
            print(f'本地没有，重新下载 {日期}')
            下载tushare数据(日期, 日期)
        else:
            if count_csv_lines(日K文件路径) < 10:
                print(f'本地数据为空，重新下载 {日期}')
                os.remove(日K文件路径)
                下载tushare数据(日期, 日期)

    if 日K:
        # 读取本地 日K数据
        日K文件路径 = os.path.join(本地tushare缓存路径, '日K数据')
        读取文件夹所有csv文件(日K文件路径, sDate, eDate)

    if 涨跌停:
        # 读取本地 涨跌停数据
        涨跌停文件路径 = os.path.join(本地tushare缓存路径, '涨跌停')
        读取文件夹所有csv文件(涨跌停文件路径, sDate, eDate)

    if 除权息:
    # 读取本地 除权息数据
        除权息文件路径 = os.path.join(本地tushare缓存路径, '除权息')
        读取文件夹所有csv文件(除权息文件路径, sDate, eDate)

    if 停牌:
    # 读取本地 停牌数据
        停牌文件路径 = os.path.join(本地tushare缓存路径, '停牌')
        读取文件夹所有csv文件(停牌文件路径, sDate, eDate)

    return g_tushare


# 乖n日：包括今天，近n天未触及涨跌停、除权息、停牌 【注意：如果异常情况也返回True，剔除该数据】
def 是否是乖n日(日期, n日, 未来一天交易日是否属于乖日, 交易日历, symbol):
    # t0 = time.time()
    if 日期 not in 交易日历:
        print('处理日期错误!!!，不在交易日期里')
        exit()

    结束日期index = 交易日历.index(日期)
    开始日期index = 结束日期index + 1 - n日
    # 处理边界问题，比如第5日和乖5日
    if 开始日期index  < 0:
        # print('处理边界数据异常!!!，在[%s] 乖乖[%d]日 超出了交易日历 开始时间' %(日期, n日))
        return True

    if 未来一天交易日是否属于乖日:
        结束日期index += 1
    if len(交易日历) < 结束日期index + 1:
        # print('处理边界数据异常!!!，在[%s] 乖乖[%d]日 超出了交易日历 结束时间' %(日期, n日))
        return True
    
    for i in range(结束日期index - 开始日期index + 1):
        index = i + 开始日期index
        # 通过日期和代码 是否存在除权息、停牌
        date = 交易日历[index]
        
        if symbol in g_tushare['除权息'][date]:
            return True

        if symbol in g_tushare['停牌'][date]:
            return True
        
        if symbol not in g_tushare['日K数据'][date]:
            print('[%s] 在 [%s] 可能停牌了，tushare停牌数据不准确' % (symbol, 日期))
            return True
        if symbol not in g_tushare['涨跌停'][date]:
            return True

        high = float(g_tushare['日K数据'][date][symbol][0])
        low = float(g_tushare['日K数据'][date][symbol][1])

        zt = float(g_tushare['涨跌停'][date][symbol][0])
        dt = float(g_tushare['涨跌停'][date][symbol][1])

        if abs(high - zt) < 0.00001 or abs(low - dt) < 0.00001:
            return True
    # t1 = time.time()
    # print('处理乖耗时 %d微秒' % ((t1-t0) * 1000000))
    return False

def 尾盘做多每日代码池(日期, 交易日历, num):
    path = '/home/andy/Damon/Strategy/数据文件/乖5日代码池/'
    if num == 1:
        path = '/home/andy/Damon/Strategy/数据文件/乖1日代码池/'
    if not os.path.exists(path):
        os.makedirs(path)
    文件路径 = path + 日期 + '.csv'
    if os.path.exists(文件路径):
        return

    # 每日能正常交易，且上市满365天
    symbols = []
    datas = pro.stock_basic(list_status='L', fields='symbol, name, market, list_status, list_date')
    for data in datas.values:
        # 获取全市场正常交易的代码池，剔除上市未满3个月的
        if 比较两个日期间隔时间(data[4], 日期, 365):
            symbols.append(data[0])

    # 获取当日的日K数据
    dayData = pro.daily(trade_date=日期)

    map = {}
    for day in dayData.values:
        symbol = day[0][:6]
        if symbol not in set(symbols):
        # 剔除上市未满365天
            continue

        if 是否是乖n日(日期, num, True, 交易日历, symbol):
            continue
        map[symbol] = day[5]

    # 计算下一个交易日期
    index = 交易日历.index(日期)
    if index+1 == len(交易日历):
        return
    

    下一个交易日期 = 交易日历[index+1]
    下一日涨跌停列表 = 获取涨跌停数据(下一个交易日期)
    # 获取下一个交易日的日K数据
    nextData = pro.daily(trade_date=下一个交易日期)
    for data in nextData.values:
        symbol = day[0][:6]
        # 最高价 == 跌停价
        if symbol in set(map) and abs(data[3] - 下一日涨跌停列表[symbol][1]) < 0.00001:
            map.pop(symbol, None)

    with open(文件路径, 'w', newline='', encoding='utf_8_sig') as f:
        writer = csv.writer(f)
        for key in map:
            writer.writerow([key, str(map[key])])
    print('当前日期 %s %d 剩余[%d]天' % (日期, 交易日历.index(日期)+1, len(交易日历)-交易日历.index(日期)-1))


# 下载日K、停牌、除权除息、涨跌停数据
def 下载tushare数据(sDate, eDate):
    pool = multiprocessing.Pool(processes=4)
    for i in range(4):
        if i == 0:
            pool.apply_async(下载并缓存日K数据, (sDate, eDate))
            # 下载并缓存日K数据()
        elif i == 1:
           pool.apply_async(下载并缓存除权除息数据, (sDate, eDate))
            # 下载并缓存除权除息数据()
        elif i == 2:
            pool.apply_async(下载并缓存停牌数据, (sDate, eDate))
            # 下载并缓存停牌数据()
        elif i == 3:
            pool.apply_async(下载并缓存涨跌停数据, (sDate, eDate))
            # 下载并缓存涨跌停数据()
    # 关闭进程池
    pool.close()
    # 等待所有任务完成
    pool.join()


def 下载指数日K数据():
    # 000300.SH 沪深300 
    # 000905.SH 中证500
    # 000852.SH 中证1000
    # 932000.CSI 中证2000
    指数_map = {'000300.SH': '沪深300', '000905.SH': '中证500', '000852.SH': '中证1000', '932000.CSI': '中证2000'}
    指数列表 = ['000300.SH', '000905.SH', '000852.SH', '932000.CSI']
    for 指数代码 in 指数列表:
        指数名 = 指数_map[指数代码]
        print(指数名)
        df = pro.index_daily(ts_code=指数代码, start_date='20230831', end_date='20240815')
        指数文件路径 = '/root/Andy/Strategy/数据文件/%s.csv' % 指数名
        with open(指数文件路径, 'w') as f:
            f.write('日期,收盘价\n')
            for d in df.values.tolist():
                f.write('%s,%s\n' % (d[1], str(d[2])))

def 缓存所有票的复权因子():
    全量因子_map = defaultdict(lambda: defaultdict(float))
    代码_名称 = 获取股票名称()
    codes = list(代码_名称.keys())
    # codes = ['301277']
    for i in range(len(codes)):
        print(f"剩余{len(codes) - i}")
        code = codes[i]
        ts_code = code + '.SZ'
        if int(code) >= 600000:
            ts_code = code + '.SH'
        df = pro.adj_factor(ts_code=ts_code, trade_date='')
        last_因子 = 0
        v = df.values.tolist()
        v.reverse()
        for d in v:
            日期 = d[1]
            if int(日期) < 20150101:
                break
            因子 = d[2]
            if last_因子 != 因子:
                全量因子_map[code][日期] = 因子
                last_因子 = 因子
    文件路径 = f'{g_currentFileDir}/所有因子.csv'
    with open(文件路径, 'w') as f:
        f.write('代码,日期,因子' + '\n')
        for code in 全量因子_map:
            for 日期 in 全量因子_map[code]:
                row = [code]
                row.append(日期)
                row.append(str(全量因子_map[code][日期]))
                f.write(','.join(row) + '\n')


if __name__ == "__main__":
    # 下载指数日K数据()
    # exit()

    # 删除代码()

    开始日期 = '20250729'
    结束日期 = '20250729'

    # 日期列表 = 获取交易日历(开始日期, 结束日期)
    # for 日期 in 日期列表:
    #     print(日期)
    #     下载每日指标(日期)

    下载tushare数据(开始日期, 结束日期)


    print('结束任务')