import os
import 更新tushare数据
import time
from datetime import datetime
from collections import defaultdict

from datetime import datetime
from dateutil.relativedelta import relativedelta

import multiprocessing

import 工具

g_currentFileDir = os.path.dirname(os.path.abspath(__file__))

g_code = ''
g_日期 = ''

# g_code = '603508'
# g_日期 = '20240514'


# 还需要增加一个逻辑，如果当前是突然猛的上涨，这种票大概率会亏钱，需要前面30天内，至少有一天还存在一个涨幅较高的 释放过底部一次压力 这次是至少是第二次上冲
def 判断当前票是否最近最高收盘价(代码, 当天日期, 全量日历, tushare_map, 全量因子_map, 天数=60, 当日最小涨幅=0.05, 最大涨幅 = 1.2):
    idx = 全量日历.index(当天日期)
    if idx >= len(全量日历):
        print(f'{代码} {当天日期} 全量日历 不够 {天数}')
    i = idx - 天数 + 1
    if i < 0:
        i = 0
    当天收盘价 = float(tushare_map['日K数据'][当天日期][代码][3])
    当天昨收价 = float(tushare_map['日K数据'][当天日期][代码][4])
    当前涨跌幅 = 当天收盘价/当天昨收价 - 1
    if 当前涨跌幅 < 当日最小涨幅:
        return [False]
    前多少天的最低收盘价 = 100000
    while i <= idx:
        日期 = 全量日历[i]
        if not 代码 in tushare_map['日K数据'][日期]:
            i += 1
            continue
        收 = float(tushare_map['日K数据'][日期][代码][3])
        前多少天的最低收盘价 = min(前多少天的最低收盘价, 收)
        转后价格 = 工具.根据因子转换价格(代码, 收, 日期, 当天日期, 全量因子_map)
        if 转后价格 != 收:
            # print(f'{代码} 在 {日期} 价格做了转换 {收} 转为 {转后价格}')
            pass
        if 转后价格 > 当天收盘价:
            return [False]
        i += 1
    
    最高涨幅 = 当天收盘价/前多少天的最低收盘价 - 1
    if 最高涨幅 > 最大涨幅:
        # print(f'{代码} {日期} {round(最高涨幅, 2)} 涨太多了 被剔除')
        return [False]
    
    return [True]

def 获取均线值(交易日历, 日期, n, code, tushare_map):
    c_idx = 交易日历.index(日期)
    if c_idx < n-1:
        print(f"{日期} 在 {交易日历[0]} - {交易日历[-1]} 中 没有 {n}个交易日")
        return 0
    价格数组 = []
    收盘价 = 0
    while c_idx >= 0:
        当前日期 = 交易日历[c_idx]
        if code in tushare_map['日K数据'][当前日期]:
            收盘价 = float(tushare_map['日K数据'][当前日期][code][3])
            价格数组.append(收盘价)
        c_idx -= 1
        if len(价格数组) == n:
            break
    if len(价格数组) != n:
        print(f'{日期} {code} 均线值有问题')
        return
    均值 = sum(价格数组)/len(价格数组)
    return 均值

# 卖出逻辑
def 卖出逻辑(交易日历, 日期, code, 成本价, tushare_map, 买入次数):
    收盘价 = float(tushare_map['日K数据'][日期][code][3])
    if 收盘价/成本价 - 1 <= -0.1:
        # 低于成本价10个点 卖出
        return [True, 收盘价]

    均值 = 获取均线值(交易日历, 日期, 10, code, tushare_map)
    # if 收盘价 < 均值 and 买入次数 > 1:
    if 收盘价 < 均值:
        # 低于10日均线 卖出
        return [True, 收盘价]
    
    return [False, 收盘价]

def 读取所有因子():
    全量因子_map = {}
    文件路径 = f'{g_currentFileDir}/所有因子.csv'
    with open(文件路径, 'r') as f:
        lines = f.readlines()
        lines.pop(0)
        for line in lines:
            v = line.replace('\n', '').split(',')
            code = v[0]
            日期 = v[1]
            因子 = v[2]
            if code not in 全量因子_map:
                全量因子_map[code] = {}
            全量因子_map[code][日期] = 因子
    return 全量因子_map
def 根据日期获取代码因子(code, 日期, 全量因子_map):
    因子 = 0
    if code not in 全量因子_map:
        print(f'{code} {日期} 因子数据不存在')
        return 因子
    日期数组 = list(全量因子_map[code].keys())
    日期数组.sort(reverse=True)
    for i in range(len(日期数组)):
        if int(日期) >= int(日期数组[i]):
            因子 = float(全量因子_map[code][日期数组[i]])
            break
    return 因子

def 根据因子转换价格(code, 需转价格, 需转日期, 当前日期, 全量因子_map):
    # 获取该股票的所有日期，并按降序排序
    if code not in 全量因子_map:
        # 一直未进行除权除息 无需转换
        return 需转价格
    日期数组 = list(全量因子_map[code].keys())
    日期数组.sort(reverse=True)  # 降序排列
    
    # 如果日期数组为空，直接返回需要转换
    if not 日期数组:
        return 需转价格
    
    # 遍历日期数组，检查需转日期和当前日期是否在同一个区间
    for i in range(len(日期数组) - 1):
        当前区间开始 = int(日期数组[i])
        当前区间结束 = int(日期数组[i + 1])  # 右开区间
        
        # 检查需转日期和当前日期是否都在 [当前区间开始, 当前区间结束) 内
        if (当前区间开始 <= int(需转日期) < 当前区间结束) and (当前区间开始 <= int(当前日期) < 当前区间结束):
            # 不需要转换
            return 需转价格
    
    # 特殊情况处理：如果日期数组只有一个日期，检查是否在该日期当天
    if len(日期数组) == 1:
        单一日 = int(日期数组[0])
        if 单一日 <= int(需转日期) and 单一日 <= int(当前日期):
            # 不需要转换
            return 需转价格

    之前因子 = 根据日期获取代码因子(code, 需转日期, 全量因子_map)
    现在因子 = 根据日期获取代码因子(code, 当前日期, 全量因子_map)
    转后价格 = round(需转价格*之前因子/现在因子, 2)
    return 转后价格

def 找到几个月前的日期(日期, 几个月前):
    # 输入日期（需转换为整数）
    input_date = int(日期)

    # 解析为年、月、日
    year = input_date // 10000
    month = (input_date % 10000) // 100
    day = input_date % 100

    # 创建datetime对象
    date_obj = datetime(year, month, day)

    # 计算3个月前的日期
    three_months_ago = date_obj - relativedelta(months=3)

    # 格式化输出结果
    result = three_months_ago.strftime("%Y%m%d")
    print(result)  # 输出：20231101
    return result

# 需要单独抽离出 核心判断逻辑 进行一字板、当天涨停、换手率等因子进行 业绩回测
# def 多维度因子判断(日期, code, tushare_map, 涨停才下单, 不涨停才下单, 换手率范围内才下单):
#     if 涨停才下单 == True:
        

def 开始处理(交易日历, 全量日历, 代码名称_map, 每日指标_map, tushare_map, 全量因子_map, 维度, value):
    print(f'开始处理 {维度} {value}')
    当前持仓信息 = {}
    交易记录 = []
    交易次数 = 0

    总本金 = 100000
    for 日期 in 交易日历:
        if 日期 == 交易日历[-1]: break
        if g_日期 != '' and 日期 != g_日期: continue

        # 检查当前持仓 是否需要加仓和卖出
        for code in list(当前持仓信息.keys()):
            if g_code != '' and code != g_code: continue

            v = 当前持仓信息[code]
            if len(v) >= 1:
                首次建仓成本 = v[0][2]
                最近建仓日期 = v[-1][1]
                最近建仓成本 = v[-1][2]

                # 在下一日开盘才建仓，避免同一天 既买入 又卖出
                if 最近建仓日期 == 日期:continue
                if code not in tushare_map['日K数据'][日期]:
                    continue
                
                # 先判断是否需要卖出
                结果 = 卖出逻辑(全量日历, 日期, code, 首次建仓成本, tushare_map, len(v))
                if 结果[0] == True:
                    盈亏率 = 0
                    盈亏额 = 0
                    卖出价格 = 结果[1]
                    本次交易记录 = ''
                    
                    for 买入 in v:
                        本次买入日期 = 买入[1]
                        本次买入价格 = 买入[2]
                        本次买入金额 = 买入[3]

                        转换后买入价格 = 根据因子转换价格(code, 本次买入价格, 本次买入日期, 日期, 全量因子_map)
                        买入[2] = 转换后买入价格

                        盈亏额 += 本次买入金额*(卖出价格/转换后买入价格-1)
                        盈亏率 = 卖出价格/本次买入价格 - 1
                        盈亏率 = 卖出价格/转换后买入价格 - 1
                        if 盈亏率 < -0.3:
                            print(f"严重亏损 {code} {买入[1]}买入 {买入[2]}  {日期} 卖出价格 {卖出价格} {盈亏率}")

                        买入.append('买入')
                        l = ','.join([str(a) for a in 买入])  + f',加仓次数,{len(v)}' + ',#,'
                        if 本次交易记录 == '':
                            本次交易记录 += l
                        # 交易记录.append(买入)
                        
                    结果[0] = 日期
                    结果.append('卖出')
                    l = ','.join(str(a) for a in 结果)
                    本次交易记录 += l
                    本次交易记录 = str(round(盈亏额, 2)) + ',' + 本次交易记录


                    结果.insert(0, code)
                    交易记录.append(本次交易记录)
                    总本金 += 盈亏额
                    交易次数 += 1
                    del 当前持仓信息[code]
                

                # 再看是否需要加仓
                收盘价 = float(tushare_map['日K数据'][日期][code][3])
                跌停价 = float(tushare_map['涨跌停'][日期][code][1])
                成交量 = int(tushare_map['日K数据'][日期][code][5])
                总股数 =  float(每日指标_map[日期][code][2])*10000
                流股数 =  float(每日指标_map[日期][code][3])*10000
                换手率 = round(成交量/流股数, 4)
                # if 收盘价 == 跌停价:
                #     # 当前跌停了，第二天开盘不下单
                #     continue
                if 收盘价/最近建仓成本 - 1 >  0.05:
                    idx = 交易日历.index(日期)
                    下一个交易日 = 交易日历[idx + 1]
                    if code not in tushare_map['日K数据'][下一个交易日]:
                        continue
                    开盘价 = float(tushare_map['日K数据'][下一个交易日][code][0])
                    涨停价 = float(tushare_map['涨跌停'][下一个交易日][code][0])

                    if 开盘价 == 涨停价:
                        # 开盘涨停就不买了
                        continue
                    if code in 当前持仓信息:
                        当前持仓信息[code].append([code, 下一个交易日, 开盘价, 5000, 换手率])
                    else:
                        当前持仓信息[code] = [[code, 下一个交易日, 开盘价, 5000, 换手率]]
        
        codes = 工具.获取代码池列表(日期, 代码名称_map, 每日指标_map[日期])
        if 维度 == '市值':
            codes = 工具.获取代码池列表(日期, 代码名称_map, 每日指标_map[日期], 市值=value)
        
        当天可建仓列表 = []
        for code in codes:
            if g_code != '' and code != g_code: continue

            if code in 当前持仓信息:
                continue
            v = 判断当前票是否最近最高收盘价(code, 日期, 全量日历, tushare_map, 全量因子_map, 天数=100, 当日最小涨幅=0.05, 最大涨幅 = 1.5)
            if v[0] == False: continue
            收盘价 = float(tushare_map['日K数据'][日期][code][3])

            idx = 交易日历.index(日期)
            下一个交易日 = 交易日历[idx + 1]
            if code not in tushare_map['日K数据'][下一个交易日]:
                continue
            开盘价 = float(tushare_map['日K数据'][下一个交易日][code][0])
            涨停价 = float(tushare_map['涨跌停'][下一个交易日][code][0])
            if 开盘价 == 涨停价:
                # 开盘涨停就不买了
                continue
            成交量 = int(tushare_map['日K数据'][日期][code][5])
            总市值 = float(每日指标_map[日期][code][0])
            总股数 =  float(每日指标_map[日期][code][2])*10000


            当日涨停价 = float(tushare_map['涨跌停'][日期][code][0])
            流股数 =  float(每日指标_map[日期][code][3])*10000
            换手率 = round(成交量/流股数, 4)


            # 出 当日收盘必须涨停 第二天才下单 近一年回测数据
            # if (当日涨停价 != 收盘价): continue

            # 出 当日收盘不能涨停 第二天才下单 近一年回测数据
            # if (当日涨停价 == 收盘价): continue

            # 出 换手率 > 30% 才下单 近一年回测数据
            # if 换手率 < 0.3: continue

            # 出 换手率 > 【20%， 30%] 才下单 近一年回测数据
            # if 换手率 < 0.2 or 换手率 > 0.3: continue

            # 出 换手率 > 【10%， 20%] 才下单 近一年回测数据
            # if 换手率 < 0.1 or 换手率 > 0.2: continue

            # 出 换手率 > 【5%， 10%] 才下单 近一年回测数据
            # if 换手率 < 0.05 or 换手率 > 0.1: continue

            # 出 换手率 < 5% 才下单 近一年回测数据
            # if 换手率 > 0.05: continue

            # 当天不能涨停, 换手率超过20%
            # if 收盘价 == 当日涨停价 or 换手率 < 0.2: continue


            当天可建仓列表.append([code, 下一个交易日, 开盘价, 5000, 换手率, 总市值])

            

            # 需要单独抽离出 核心判断逻辑 进行一字板、当天涨停、换手率等因子进行 业绩回测
            
            # 当天建仓笔数 += 1
            # 当前持仓信息[code] = [[code, 下一个交易日, 开盘价, 5000]]
            # if 当天建仓笔数 >= 50:
            #     break
        # 按照换手率 进行降序排列，选换手率最高的10个票
        sorted_data = sorted(当天可建仓列表, key=lambda x: x[4], reverse=True)
        最大笔数限制 = 10
        当天建仓笔数 = 0
        
        idx = 交易日历.index(日期)
        建仓日期 = 交易日历[idx + 1]
        for 建仓 in sorted_data[:20]:
            code = 建仓[0]
            当前持仓信息[code] = [建仓[:5]]
            当天建仓笔数 += 1
        print(f'{建仓日期} {维度} {value} 建仓笔数{当天建仓笔数}')
        
    print(f'{维度} {value} 盈亏额{总本金-100000} 交易次数{交易次数} ')
    文件夹路径 = f'{g_currentFileDir}/交易记录/新高'
    if not os.path.exists(文件夹路径):
        os.makedirs(文件夹路径)
        
    文件 = f'{文件夹路径}/{维度}_{value}.csv'
    if g_code != '':
        文件 = f'{文件夹路径}/{维度}_{g_code}_{value}.csv'
    with open(文件, 'w') as f:
        f.write('盈亏额' + '\n')
        for l in 交易记录:
            f.write(l + '\n')

def error_callback(error):
    import traceback
    traceback.print_exception(type(error), error, error.__traceback__)

if __name__=="__main__":
    代码名称_map = 更新tushare数据.获取股票名称()

    开始日期 = '20240604'
    结束日期 = '20250604'

    

    几个月前日期 = 找到几个月前的日期(开始日期, 5)

    每日指标_map = 更新tushare数据.读取每日指标(开始日期, 结束日期)
    tushare_map = 更新tushare数据.读取tushare本地缓存(日K=True, 涨跌停=True, sDate=int(几个月前日期),eDate=int(结束日期))

    全量因子_map = 读取所有因子()
    全量日历 = 更新tushare数据.获取交易日历(几个月前日期, 结束日期)
    交易日历 = 更新tushare数据.获取交易日历(开始日期, 结束日期)
    全量日历.sort()
    交易日历.sort()

    pool = multiprocessing.Pool(processes=4)
    市值列表 = [100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000]
    # 市值列表 = [600000, 700000, 800000, 900000, 1000000]
    市值列表 = [300000]
    for 市值 in 市值列表:
        开始处理(交易日历, 全量日历, 代码名称_map, 每日指标_map, tushare_map, 全量因子_map, '市值', 市值)
        # pool.apply_async(开始处理, (交易日历, 全量日历, 代码名称_map, 每日指标_map, tushare_map, 全量因子_map, '市值', 市值), error_callback=error_callback)
    # 关闭进程池
    pool.close()
    # 等待所有任务完成
    pool.join()

    