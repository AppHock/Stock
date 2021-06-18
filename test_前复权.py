import os
import tushare as ts

ts.set_token('47aca0f52e01163f8fae34938cad4b776021ff2cc1678e557b744899')
pro = ts.pro_api()

#symbol = '000930.SZ'
#df = ts.pro_bar(ts_code=symbol, adj='qfq', start_date='20210615', end_date='20210617')
#df_list = df.values.tolist()
#
#for item in df_list:
#    print(item)

起始日期 = '20200618'
结束日期 = '20210618' #即前复权相对的参考的那一天

f_result = open('以%s前复权日k数据.csv'%(结束日期), 'w', encoding='utf-8-sig')

#获取当前上市的所有股票
当前上市的所有股票_list = []

data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
df_list = data.values.tolist()

for item in df_list:
    当前上市的所有股票_list.append(item[0])

#获取前复权日k数据
index = 0
for symbol in 当前上市的所有股票_list:
    print(symbol, index)
    df = ts.pro_bar(ts_code=symbol, adj='qfq', start_date=起始日期, end_date=结束日期)
    df_list = df.values.tolist()

    for item in df_list:
        print(item, file = f_result)
    index += 1