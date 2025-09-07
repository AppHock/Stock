from datetime import datetime
from dateutil.relativedelta import relativedelta

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

def 计算日期差(d1, d2):
    # 转换为 datetime 对象
    date1 = datetime.strptime(d1, "%Y%m%d")
    date2 = datetime.strptime(d2, "%Y%m%d")
    # 计算时间差
    delta = date2 - date1
    return delta.days


# 代码池
def 获取代码池列表(日期, 代码_名称, 当日指标, 市值=100000, 上市满多少天=365):
    codes = []
    for code in 当日指标:
        总市值 = float(当日指标[code][0])
        if 总市值 <= 市值:
            # 总市值低于10亿
            continue
        if code not in 代码_名称:
            # print(f'不存在 {code}')
            continue
        上市日期 = int(代码_名称[code][1])
        if 上市日期 > int(日期):
            # 当日 还未上市
            continue
        差 = 计算日期差(str(上市日期), 日期)
        if 差 <= 上市满多少天:
            # 剔除上市不满一年 
            continue
        if code[0] != '0' and code[0] != '3' and code[0] != '6':
            continue
        codes.append(code)
    return codes