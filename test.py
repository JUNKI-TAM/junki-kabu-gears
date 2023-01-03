import sqlite3
DATABASE = 'database.db'


# kabu用import
from pandas_datareader import data
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import mplfinance as mpf
import numpy as np

# SQliteのデータベースからデータを取得のためのObjectを作成
con = sqlite3.connect(DATABASE)
# データベースの中からgearsを全て抜き出し
db_gears = con.execute('SELECT * FROM gears').fetchall()
# データベースへの接続解除
con.close()

gears = []

for row in db_gears:
    gears.append({'name':row[0],'weight':(int(row[1])),'price':row[2]})
    print(row[1])

print(gears)

x = np.array([100, 200, 300, 400, 500])
print(x)
