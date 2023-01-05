from pandas_datareader import data
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import mplfinance as mpf


# # 関数宣言

# 株動向描画
def evaluation_stock(company_name,start,end):
    #get data
    df = data.DataReader(company_name,'stooq').sort_index()
    df = df[(df.index>=start) & (df.index<=end)]

    date = df.index
    price = df['Close']

    # 単純移動平均
    ##ゴールデンクロス：短期が長期を上回る
    ##デッドクロス：短期が長期を下回る
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

    #output figure
    ## ボリンジャーバンド追加
    apds = [mpf.make_addplot(df['sma00'],color='blue'),
            mpf.make_addplot(df['sma01'],color='orange'),
            mpf.make_addplot(df['sma02'],color='green'),
            mpf.make_addplot(df['UPPER'],color='gray'),
            mpf.make_addplot(df['LOWER'],color='gray'),
            mpf.make_addplot(df['MACD'],type='bar',color='gray',width=1.0,panel=1,alpha=0.5,ylabel='MACD'),
            mpf.make_addplot(df['RSI'],type='line',panel=2,ylabel='RSI')
        ]


    mpf.plot(df,type='candle',figsize=(30,10),style = 'yahoo',volume =True,addplot=apds,
            volume_panel=3,panel_ratios=(5,2,2,1),savefig='./templates/images/technical.png')

    #株価評価
    n=5

    jdg_GorD_pre = df['sma00'].shift(n)-df['sma01'].shift(n)
    jdg_GorD_pre
    jdg_GorD_now = df['sma00']-df['sma01']

    analyze = 'CROSS: '

    if (jdg_GorD_pre[-1] > 0) and (jdg_GorD_now[-1] < 0):
        print(analyze+'Dead Cross Timing!!')
    elif (jdg_GorD_pre[-1] < 0) and (jdg_GorD_now[-1] > 0):
        print(analyze+'Goalden Cross Timing!!')
    else:
        print(analyze+'Nothing cross point')

    analyze = 'RSI: '
    if (df['RSI'][-n:]<20).sum() > 0:
        print(analyze+'TOO SEALING TIMING!')
    elif (df['RSI'][-n:]>80).sum() > 0:
        print(analyze+'TOO BUYING TIMING!')
    else:
        print(analyze+'normal operation')

    analyze = 'MACD: '
    if (df['MACD'][-n:]<-200).sum() > 0:
        print(analyze+'強下降トレンド')
    elif (df['MACD'][-n:]>200).sum() > 0:
        print(analyze+'強下降トレンド')
    elif (df['MACD'][-n:]<0).sum() > (df['MACD'][-n:]>0).sum():
        print(analyze+'弱下降トレンド')
    elif (df['MACD'][-n:]<0).sum() < (df['MACD'][-n:]>0).sum():
        print(analyze+'弱上昇トレンド')
    else:
        print(analyze+'トレンド不明')
        
    analyze = 'BBANDS: '
    jdg_BBANDS_upper = (df['UPPER']-df['Close'])<0
    jdg_BBANDS_lower = (df['LOWER']-df['Close'])>0

    if jdg_BBANDS_upper[-n:].sum()>0:
        print(analyze+'TOO BUYING TIMING!')
    elif jdg_BBANDS_lower[-n:].sum()>0:
        print(analyze+'TOO SEALING TIMING!')
    else:
        print(analyze+'normal operation')



# # メイン処理
start = '2022-01-01'
end = datetime.datetime.today().strftime("%Y-%m-%d")
#日経225は^NKX SP500は^SPX 
company_name = '^SPX'

df = evaluation_stock(company_name,start,end)


    





