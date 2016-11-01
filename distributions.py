import pandas as pd
import MySQLdb as MySQL

mysql_cn = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', passwd='R3tr0sh33t', db='retrosheet')

dataframe = pd.read_sql('select * from myevents', mysql_cn)

mysql_cn.close()

print(dataframe)