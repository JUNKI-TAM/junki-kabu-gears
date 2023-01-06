# template import
from flask import Flask,render_template, request,redirect,url_for
app = Flask(__name__, static_folder='./templates/images')
import db
db.create_gears_table()

import base64
from io import BytesIO
import sqlite3
DATABASE = 'database.db'


# kabu用import
from pandas_datareader import data
import pandas as pd
import matplotlib  # <--ここを追加
matplotlib.use('Agg')  # <--ここを追加
import matplotlib.pyplot as plt

import matplotlib.dates as mdates
import datetime
import mplfinance as mpf
import numpy as np
import japanize_matplotlib

@app.route('/')
def index():
    # SQliteのデータベースからデータを取得のためのObjectを作成
    con = sqlite3.connect(DATABASE)
    # データベースの中からgearsを全て抜き出し
    db_gears = con.execute('SELECT * FROM gears').fetchall()
    # データベースへの接続解除
    con.close()

    gears = []
    weight_l = []
    label_l = []

    for row in db_gears:
        gears.append({'name':row[0],'weight':(int(row[1])),'price':row[2]})
        label_l.append(row[0])
        weight_l.append(int(row[1]))

    cmap=plt.get_cmap('tab20b') 
    colorlist = [cmap(i) for i in range(len(weight_l))]
    x=np.array(weight_l)
    plt.clf()
    plt.pie(x,labels=label_l, startangle=90, counterclock=False,  autopct='%.1f%%', pctdistance=0.8, colors=colorlist)
    plt.title('Total:'+str(sum(weight_l))+' [g]')
    image = BytesIO()
    plt.savefig(image, format="png")
    plt.close()
    # base64 形式に変換する。
    image.seek(0)
    base64_img_pie = base64.b64encode(image.read()).decode()

    return render_template('index.html',gears=gears,img_pie=base64_img_pie)



@app.route('/form')
def form():
     return render_template('form.html')   

@app.route('/register',methods=['POST'])
def register():
    name = request.form['name']
    weight = request.form['weight']
    price = request.form['price']

    if name!='' and weight!='':
        con = sqlite3.connect(DATABASE)
        con.execute('INSERT INTO gears VALUES(?,?,?)',
                    [name,weight,price])
        con.commit()
        con.close()

    return redirect(url_for('index'))

@app.route("/delete_list/<string:list_name>")
def delete_list(list_name):
    del_cmd = 'DELETE from gears WHERE name = "' + list_name+'"'
    con = sqlite3.connect(DATABASE)
    con.execute(del_cmd)
    con.commit()
    con.close()
    return redirect(url_for('index'))

@app.route('/kabu')
def kabu():
    return render_template('kabu.html',patarn = 1)   




def jdg_stock(df,n):
    jdg_GorD_pre = df['sma00'].shift(n)-df['sma02'].shift(n)
    jdg_GorD_now = df['sma00']-df['sma02']
    analyze = 'CROSS: '
    if (jdg_GorD_pre[-1] > 0) and (jdg_GorD_now[-1] < 0):
        ans_gd='DEAD CROSS'
    elif (jdg_GorD_pre[-1] < 0) and (jdg_GorD_now[-1] > 0):
        ans_gd='GOALDEN CROSS'
    else:
        ans_gd='non cross'

    analyze = 'RSI: '
    if (df['RSI'][-n:]<20).sum() > 0:
        ans_rsi='TOO SEALING'
    elif (df['RSI'][-n:]>80).sum() > 0:
        ans_rsi='TOO BUYING'
    else:
        ans_rsi='normal operation'

    analyze = 'MACD: '
    if (df['MACD'][-n:]<-200).sum() > 0:
        ans_macd='HIGH-DOWNTREND'
    elif (df['MACD'][-n:]>200).sum() > 0:
        ans_macd='HIGH-UPTREND'
    elif (df['MACD'][-n:]<0).sum() > (df['MACD'][-n:]>0).sum():
        ans_macd='Low-Downtrend'
    elif (df['MACD'][-n:]<0).sum() < (df['MACD'][-n:]>0).sum():
        ans_macd='Low-Uptrend'
    else:
        ans_macd='non-trend'
        
    analyze = 'BBANDS: '
    jdg_BBANDS_upper = (df['UPPER']-df['Close'])<0
    jdg_BBANDS_lower = (df['LOWER']-df['Close'])>0
    if jdg_BBANDS_upper[-n:].sum()>0:
        ans_bbands='TOO BUYING TIMING'
    elif jdg_BBANDS_lower[-n:].sum()>0:
        ans_bbands='TOO SEALING TIMING'
    else:
        ans_bbands='normal operation'

    return [ans_gd,ans_rsi,ans_macd,ans_bbands]


@app.route('/eval_kabu',methods=['POST'])
def eval_kabu():
    company_name = request.form['company_name']
    start = request.form['start']
    
    if request.form['end'] == 'today':
        end = datetime.datetime.today().strftime("%Y-%m-%d")
    else:
        end = request.form['end']

    ans_gd_s=[]
    ans_rsi_s=[]
    ans_macd_s=[]
    ans_bbands_s=[]
    ans_gd_m=[]
    ans_rsi_m=[]
    ans_macd_m=[]
    ans_bbands_m=[]
    ans_gd_l=[]
    ans_rsi_l=[]
    ans_macd_l=[]
    ans_bbands_l=[]
    base64_img_close=[]
    base64_img_vol=[]
    base64_img_rsi=[]
    

    if (company_name!='' and start!='' and end!=''):
        patarn=2
        #get data
        df = data.DataReader(company_name,'stooq').sort_index()
        df = df[(df.index>=start) & (df.index<=end)]
        date = df.index
        price = df['Close']

        # 分析指標算出
        # 単純移動平均
        ##ゴールデンクロス：短期が長期を上回る 買い時
        ##デッドクロス：短期が長期を下回る　売り時
        span00 = 5
        span01 = 25
        span02 = 50
        df['sma00']=price.rolling(window=span00).mean()
        df['sma01']=price.rolling(window=span01).mean()
        df['sma02']=price.rolling(window=span02).mean()
        # ボリンジャーバンド
        n=25
        bjb_std = price.rolling(window=n).std()
        df['UPPER'] = df['sma01'] + bjb_std*2
        df['LOWER'] = df['sma01'] - bjb_std*2
        
        #MACD
        ##MACD線 ＝ 短期移動平均線（EMA） － 長期移動平均線（EMA）　（例：12週線 － 26週線）
        ##ｎ日EMA＝（EMAy×（ｎ－1）＋P×2）÷（ｎ＋1）
        ema_01=price.copy()
        n=12
        tmp = 0
        emay = 0
        for indx in price.index:
            if tmp == 0:        
                ema_01[indx]=price[indx]
                tmp += 1
            else:
                ema_01[indx]=(emay*(n-1)+price[indx]*2)/(n+1)
            emay = ema_01[indx]
        ema_02=price.copy()
        n=26
        tmp = 0
        emay = 0
        for indx in price.index:
            if tmp == 0:        
                ema_02[indx]=price[indx]
                tmp += 1
            else:
                ema_02[indx]=(emay*(n-1)+price[indx]*2)/(n+1)
            emay = ema_02[indx]
        macd_line = ema_01-ema_02
        ##シグナル ＝ MACDの単純移動平均線（例：9週線）
        macd_signal=price.copy()
        n=9
        tmp = 0
        emay = 0
        for indx in price.index:
            if tmp == 0:        
                macd_signal[indx]=macd_line[indx]
                tmp += 1
            else:
                macd_signal[indx]=(emay*(n-1)+macd_line[indx]*2)/(n+1)
            emay = macd_signal[indx]
        ##ヒストグラム（OSCI） ＝ MACD線 － シグナル
        df['MACD'] = macd_line-macd_signal
        
        #RSI
        #① RS＝（n日間の終値の上昇幅の平均）÷（n日間の終値の下落幅の平均）
        #② RSI= 100　-　（100　÷　（RS+1））
        n=14
        rsi_tmp = price-price.shift(1)
        rsi_p = [None if i < 0 else i for i in rsi_tmp]
        rsi_p = pd.Series(rsi_p).rolling(window=n, min_periods=1).mean()
        rsi_m = [None if i > 0 else -i for i in rsi_tmp]
        rsi_m
        rsi_m = pd.Series(rsi_m).rolling(window=n, min_periods=1).mean()
        rsi_rs = rsi_p/rsi_m
        rsi = 100 - (100/(1+rsi_rs))
        rsi.index = df.index
        df['RSI']=rsi



        #株価評価
        #日単位
        [ans_gd_s,ans_rsi_s,ans_macd_s,ans_bbands_s] = jdg_stock(df,1)
        #週単位
        [ans_gd_m,ans_rsi_m,ans_macd_m,ans_bbands_m] = jdg_stock(df,7)
        #月単位
        [ans_gd_l,ans_rsi_l,ans_macd_l,ans_bbands_l] = jdg_stock(df,30)
        
        image = BytesIO()
        
        plt.clf()
        plt.figure(figsize=(10,5))
        plt.plot(date,df['Close'],label="Close",color='black')
        plt.plot(date,df['sma00'],label="short")
        plt.plot(date,df['sma01'],label="middle")
        plt.plot(date,df['sma02'],label="long")
        plt.fill_between(date,df["UPPER"],df["LOWER"],color='gray',alpha=0.2)
        plt.legend()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%y/%m"))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.gcf().autofmt_xdate()
        plt.grid(linestyle='dotted')
        plt.savefig(image, format="png")
        # base64 形式に変換する。
        image.seek(0)
        base64_img_close = base64.b64encode(image.read()).decode()

        plt.clf()
        plt.figure(figsize=(10,2))
        plt.bar(date,df["Volume"],label="Volume",color='gray')
        plt.legend()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%y/%m"))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.gcf().autofmt_xdate()
        plt.grid(linestyle='dotted')
        image = BytesIO()
        plt.savefig(image, format="png")
        # base64 形式に変換する。
        image.seek(0)
        base64_img_vol = base64.b64encode(image.read()).decode()

        plt.clf()
        plt.figure(figsize=(10,5))
        plt.plot(date,df["RSI"],label="RSI",color='gray')
        plt.ylim(0,100)
        plt.hlines([20,80],datetime.datetime.strptime(start,"%Y-%m-%d").date(),datetime.datetime.strptime(end,"%Y-%m-%d").date(),"gray",linestyles="dashed")
        plt.legend()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%y/%m"))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.gcf().autofmt_xdate()
        plt.grid(linestyle='dotted')
        image = BytesIO()
        plt.savefig(image, format="png")
        plt.close()
        # base64 形式に変換する。
        image.seek(0)
        base64_img_rsi = base64.b64encode(image.read()).decode()
    else:
        patarn=3

    return render_template('kabu.html', 
    stock_name = company_name,start=start,end=end,patarn=patarn,
    gd_s = ans_gd_s,rsi_s = ans_rsi_s,macd_s = ans_macd_s,bbands_s = ans_bbands_s,
    gd_m = ans_gd_m,rsi_m = ans_rsi_m,macd_m = ans_macd_m,bbands_m = ans_bbands_m,
    gd_l = ans_gd_l,rsi_l = ans_rsi_l,macd_l = ans_macd_l,bbands_l = ans_bbands_l,
    img_cls=base64_img_close,img_vol=base64_img_vol,img_rsi=base64_img_rsi)


if __name__ =='__main__':
    app.run()