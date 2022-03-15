from datetime import datetime, timedelta
import queue
from sqlite3 import Row, Timestamp
import statistics
from tkinter.tix import WINDOW

from matplotlib.axis import XAxis
import ta
from matplotlib.pyplot import axis, title
import streamlit as st
import pandas as pd 
import yfinance as yf
import yahoo_fin.stock_info as si
import webbrowser as wb
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from datetime import date
from operator import attrgetter
from plotly.subplots import make_subplots
from data import sp_500_tickers

#Set wide page layout
st.set_page_config(layout="wide")

# Get the list of S&P500 tickers
sp_500_ticker= sp_500_tickers

#Create a selectbox with the tickers
TICKER = st.sidebar.selectbox(
    'Select Stock Ticker',
    (sp_500_ticker),
    key='ticker_key'
    )

#Create a selectbox with the type of analysis
ANALYSIS = st.sidebar.selectbox(
    'Choose Analysis Type',
    ('Fundamental Analysis', 'Technical Analysis','Strategy Backtest'),
    key='analysis_key'
)

########################### Fundamental Analysis ###################################

if (ANALYSIS=='Fundamental Analysis'):

    #Seperate the page in three columns and 
    # print the logo image, the Company name and sector it belongs    
    st.header("Fundamental Analysis")
    col1,col2,col3=st.columns(3)
    #download the stock information 
    info_data = yf.Ticker(TICKER).info
    with col2:
        st.image(info_data['logo_url'])
    with col1:
        st.header(info_data['longName'])
    with col3:
        st.subheader(f"Sector: {info_data['sector']}")
    st.markdown('**Business Summary:** '+info_data['longBusinessSummary'])

    #prepare the data
    list_of_keys = info_data.keys()
    info_df= pd.DataFrame(columns=info_data.keys())
    info_df=info_df.append(
     pd.Series(info_data.values(),index=info_data.keys()),ignore_index=True
    )
    
    st.subheader('**Summary**')
    #Seperate the Summary Section in two collums and print the relevant data
    col1, col2 = st.columns(2)
    with col1:
        
        st.write('**Previous Close:**',str(info_df['previousClose'].values[0]))
        st.write('**Open**:',str(info_df['open'].values[0]))
        st.write('**Bid**:',str(info_df['bid'].values[0]),' x ',str(info_df['bidSize'].values[0]))
        st.write('**Ask**:',str(info_df['ask'].values[0]),' x ',str(info_df['askSize'].values[0]))
        st.write('**Day\'s Range**:',str(info_df['regularMarketDayLow'].values[0]),' - ',str(info_df['regularMarketDayHigh'].values[0]))
        st.write('**52 Week Range**:',str(info_df['fiftyTwoWeekLow'].values[0]),' - ',str(info_df['fiftyTwoWeekHigh'].values[0]))
        st.write('**Volume**:',str(info_df['regularMarketVolume'].values[0]))
        st.write('**Avg. Volume**:',str(info_df['averageVolume'].values[0]))

    with col2:
        st.write('**Market Cap:**',str(info_df['marketCap'].values[0]))
        st.write('**Beta(5Y Monthly):**',str(info_df['beta'].values[0]))
        if 'trailingPE' in info_df.index:
            st.write('**PE Ration (TTM):**',str(info_df['trailingPE'].values[0]))
        st.write('**EPS (TTM):**:',str(info_df['trailingEps'].values[0]))
        # st.write("**Earnings Date:**",str(calendar.iloc[0,0].strftime('%d/%m/%Y')),' - ',str(calendar.iloc[0,1].strftime('%d/%m/%Y')))
        if info_df['dividendYield'].values[0]!= None:
            st.write('**Forward Dividend & Yield**:',str(info_df['dividendRate'].values[0]),' (',str(info_df['dividendYield'].values[0]*(100)),'%)')
            st.write("**Ex-Dividend Date**",str(datetime.fromtimestamp(info_df['exDividendDate'].values[0]).strftime('%d/%m/%Y')))
        st.write('**1y Target Est:**',str(info_df['targetMeanPrice'].values[0]))

    #The rest of the data show them as a dataframe
    SHOW_STATS=st.checkbox("Show Statistics",value=True)
    if SHOW_STATS:
        st.subheader('**Statistics**')
        st.dataframe(si.get_stats(TICKER).dropna(axis=0))
    SHOW_FINANCIALS= st.checkbox("Show Financials",value=True)
    if SHOW_FINANCIALS:
        st.subheader('**Financials**')
        st.dataframe(yf.Ticker(TICKER).financials.dropna(axis=0))



########################## Tenchical Analysis ############################
if (ANALYSIS=='Technical Analysis'):
    st.title("Technical Analysis")
    
  

    
    st.subheader(yf.Ticker(TICKER).info['longName'])
    
    
    #Get END_DATE into session_state 
    if 'END_DATE' not in st.session_state:
     st.session_state.END_DATE = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
     #print(f'1rst run: st.session_state.START_DATE: {st.session_state.END_DATE}')
     #print(type(st.session_state.END_DATE))
     if 'START_DATE' not in st.session_state:
        st.session_state.START_DATE = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        #print(f'1rst run:st.session_state.END_DATE: {st.session_state.START_DATE}')
        #print(type(st.session_state.START_DATE))
        data_df=pd.DataFrame()
        #print(f'BEFORE TICKER CALL:({st.session_state.START_DATE},{st.session_state.END_DATE})',)
        #print(f'st.session_state AFTER========>{st.session_state}')

    data_df = yf.download(TICKER.lower(),start=st.session_state.START_DATE , end=st.session_state.END_DATE)

    #define the first date range (1 year)
    YESTERDAY=date.today()-timedelta(days=1)
    DEFAULT_START=YESTERDAY - timedelta(days=365)
    
    st.sidebar.markdown("***Get Historic Data***")
    START = st.sidebar.date_input("From", value=DEFAULT_START, max_value=YESTERDAY - timedelta(days=1))
    END = st.sidebar.date_input("Until", value=YESTERDAY, max_value=YESTERDAY, min_value=START)

    
    #Get new data only if the button Retrieve New Data is pressed
    if st.sidebar.button('Retrieve New Data'):
        st.session_state.START_DATE=START
        st.session_state.END_DATE=END
        #print(f'st.session_state.START_DATE={st.session_state.START_DATE},START={START}')
        
        data_df=pd.DataFrame()
        #print(f'AFTER BUTTON PRESS TICKER CALL:({st.session_state.START_DATE},{st.session_state.END_DATE})',)
        data_df = yf.download(TICKER.lower(),start=st.session_state.START_DATE , end=st.session_state.END_DATE)
        
    
    
    #Plot the close price 

    fig = go.Figure()
    fig = go.Scatter(x=data_df.index, y=data_df['Close'])
    fig = px.line(data_df,x=data_df.index,y='Close')
    st.plotly_chart(fig,use_container_width=True)
    fig.update_xaxes(
        rangebreaks = [
            dict(bounds=['sat','mon'])
        ]
    )

    # Create 4 subplots and mention plot grid size
    # Subplot logic row 1 is always OHLC chart
    # Next rows in order of priority Volume, RSI, MACD. The rest of the indicators 
    # are plotted in the OHLC chart
    fig2 = go.Figure()
    fig2 = make_subplots(rows=4, cols=1,  
               vertical_spacing=0.01, 
               row_heights=[8,3,3,3]
               )
   
    # Plot OHLC on 1st row
    fig2.add_trace(go.Candlestick(x=data_df.index, open=data_df["Open"], high=data_df["High"],
                low=data_df["Low"], close=data_df["Close"], name="OHLC",xaxis='x'), 
                row=1, col=1,
    )
   
    fig2.update_xaxes(dtick='M1',tickformat='%d/%m/%Y',row=1,col=1) 
    fig2.update_layout(title = 'Interactive CandleStick Chart',
    yaxis1_title = 'Stock Price ($)',
    xaxis1_title = 'Date/Time',
    xaxis1_rangeslider_visible = False,
    xaxis2_rangeslider_visible = False,
    height=900,
    width=1100)

    fig2.update_xaxes(
        rangebreaks = [
            dict(bounds=['sat','mon'])
        ]
    )
    #add indicators 
    add_indicators = st.checkbox('Add Indicators')
    if add_indicators:
        #st.plotly_chart(fig, use_container_width=True)
        multiselect=st.multiselect('Select Indicators',['VOLUME','RSI','SMA','MACD','EMA','BBANDS'],['VOLUME'])
        if 'BBANDS' in multiselect:
            BBANDS_SETTINGS=st.sidebar.checkbox('BBANDS Settings')
            BBANDS_WINDOW=20
            BBANDS_ST_DEV=2
            if BBANDS_SETTINGS:
                BBANDS_WINDOW=st.sidebar.number_input('BBANDS Day Window',min_value=2,max_value=100,value=20,step=1)
                BBANDS_ST_DEV=st.sidebar.number_input('BBANDS ST. DEV',min_value=1,max_value=5,value=2,step=1)
            data_df['BBNDS High Band']=ta.volatility.BollingerBands(data_df['Close'],window=BBANDS_WINDOW,window_dev=BBANDS_ST_DEV).bollinger_hband()
            data_df['BBNDS Low Band']=ta.volatility.BollingerBands(data_df['Close'],window=BBANDS_WINDOW,window_dev=BBANDS_ST_DEV).bollinger_lband()
            data_df['BBNDS Middle Band']=ta.volatility.BollingerBands(data_df['Close'],window=BBANDS_WINDOW,window_dev=BBANDS_ST_DEV).bollinger_mavg()
            fig2.add_trace(go.Scatter(x=data_df.index, y=data_df['BBNDS High Band'],mode='lines',name='BBNDS High Band',marker_color='red'), row=1, col=1)
            fig2.add_trace(go.Scatter(x=data_df.index, y=data_df['BBNDS Low Band'],mode='lines',name='BBNDS Low Band',marker_color='red'), row=1, col=1)
            fig2.add_trace(go.Scatter(x=data_df.index, y=data_df['BBNDS Middle Band'],mode='lines',name='BBNDS Middle Band',marker_color='black'), row=1, col=1)               
        if 'EMA' in multiselect:
            EMA_SETTINGS=st.sidebar.checkbox('EMA Settings')
            EMA_WINDOW=12
            if EMA_SETTINGS:
                EMA_WINDOW=st.sidebar.number_input('EMA Day Window',min_value=2,max_value=100,value=14,step=1)
            data_df['EMA']=ta.trend.ema_indicator(data_df['Close'],window=EMA_WINDOW)
            fig2.add_trace(go.Scatter(x=data_df.index, y=data_df['EMA'],mode='lines',name='EMA',marker_color='blue'), row=1, col=1)
        if 'SMA' in multiselect:
            SMA_SETTINGS=st.sidebar.checkbox('SMA Settings')
            SMA_WINDOW=12
            if SMA_SETTINGS:
                SMA_WINDOW=st.sidebar.number_input('SMA Day Window',min_value=2,max_value=100,value=12,step=1)
            data_df['SMA']=ta.trend.sma_indicator(data_df['Close'],window=SMA_WINDOW)
            fig2.add_trace(go.Scatter(x=data_df.index, y=data_df['SMA'],mode='lines',name='SMA',marker_color='yellow'), row=1, col=1)
        if 'RSI' in multiselect:
            RSI_SETTINGS=st.sidebar.checkbox('RSI Settings')
            RSI_LENGTH=14
            RSI_LOWERBAND=30
            RSI_UPPERBAND=70
            if RSI_SETTINGS:
                RSI_UPPERBAND=st.sidebar.number_input('RSI: Upper Band',min_value=0,max_value=100,value=70,step=1)
                RSO_LOWERBAND=st.sidebar.number_input('RSI: Lower Band',min_value=0,max_value=100,value=30,step=1)
                RSI_LENGTH=st.sidebar.number_input('RSI: Length',min_value=1,max_value=100,value=14,step=1)
            data_df['RSI']=ta.momentum.RSIIndicator(close=data_df['Close'],window=RSI_LENGTH).rsi()
            if 'VOLUME' in multiselect:
                ROW=3
                fig2.update_layout(
                yaxis1_title = 'Stock Price ($)',
                yaxis2_title = 'Volume (M)',
                yaxis3_title = 'RSI',
                xaxis1_title = None ,
                xaxis2_title = None,
                xaxis3_title = 'Date/Time',
                xaxis1_rangeslider_visible = False,
                xaxis2_rangeslider_visible = False,
                )
            else:
                ROW=2
                fig2.update_layout(
                yaxis1_title = 'Stock Price ($)',
                yaxis2_title = 'RSI',
                xaxis1_title = None ,
                xaxis2_title = 'Date/Time',
                xaxis1_rangeslider_visible = False,
                xaxis2_rangeslider_visible = False,
                )
            fig2.add_trace(go.Scatter(x=data_df.index,mode='lines', y=data_df['RSI'],name='RSI'), row=ROW, col=1)
            fig2.add_hline(y=RSI_UPPERBAND,name='UpperBand',row=ROW,col=1)
            fig2.add_hline(y=RSI_LOWERBAND,name='LowerBand',row=ROW,col=1)
           
        if 'VOLUME' in multiselect:
                fig2.update_layout(
                yaxis1_title = 'Stock Price ($)',
                yaxis2_title = 'Volume',
                xaxis1_title = None ,
                xaxis2_title = 'Date/Time',
                xaxis1_rangeslider_visible = False,
                xaxis2_rangeslider_visible = False,
                )
                fig2.add_trace(go.Bar(x=data_df.index, y=data_df['Volume'],name='Volume'), row=2, col=1)
        if 'MACD' in multiselect:
            MACD_FAST = 12
            MACD_SLOW = 26
            MAD_SINGAL =9 
            if st.checkbox('MACD Settings'):
                MACD_FAST= st.sidebar.number_input('MACD Fast',min_value=0,max_value=100,value=12,step=1)
                RSI_UPPERBAND=st.sidebar.number_input('MACD Slow',min_value=0,max_value=100,value=26,step=1)
                MAD_SINGAL=st.sidebar.number_input('MACD Singal',min_value=0,max_value=100,value=9,step=1)
            data_df['MACD Line']=ta.trend.MACD(data_df['Close'],MACD_FAST,MACD_SLOW,MAD_SINGAL).macd()
            data_df['MACD Histogram']=ta.trend.MACD(data_df['Close'],MACD_FAST,MACD_SLOW,MAD_SINGAL).macd_diff()
            data_df['MACD Signal Line']=ta.trend.MACD(data_df['Close'],MACD_FAST,MACD_SLOW,MAD_SINGAL).macd_signal()
            if 'VOLUME' not in multiselect:
                if 'RSI' in multiselect:
                    ROW=3
                    fig2.update_layout(
                    yaxis1_title = 'Stock Price ($)',
                    yaxis2_title = 'RSI',
                    yaxis3_title = 'MACD',
                    xaxis1_title = None ,
                    xaxis2_title = None ,
                    xaxis3_title = 'Date/Time',
                    xaxis1_rangeslider_visible = False,
                    xaxis2_rangeslider_visible = False,
                    )
                else:
                    ROW=2
                    fig2.update_layout(
                    yaxis1_title = 'Stock Price ($)',
                    yaxis2_title = 'MACD',
                    xaxis1_title = None ,
                    xaxis2_title = 'Date/Time' ,
                    xaxis1_rangeslider_visible = False,
                    xaxis2_rangeslider_visible = False,
                    )
            else:
                if 'RSI' in multiselect:
                    ROW=4
                    fig2.update_layout(
                    yaxis1_title = 'Stock Price ($)',
                    yaxis2_title = 'Volume',
                    yaxis3_title = 'RSI',
                    yaxis4_title = 'MACD',
                    xaxis1_title = None ,
                    xaxis2_title = None ,
                    xaxis3_title = None ,
                    xaxis4_title = 'Date/Time',
                    xaxis1_rangeslider_visible = False,
                    xaxis2_rangeslider_visible = False,
                    )
                else:
                    ROW =3
            fig2.add_trace(go.Bar(x=data_df.index, y=data_df['MACD Histogram'],name='MACD Histogram',marker=dict(color=(data_df['MACD Histogram']<0).astype('int'),colorscale=[[1,'red'],[0,'green']]), showlegend=False), row=ROW, col=1)
            fig2.add_trace(go.Scatter(x=data_df.index,mode='lines',y=data_df['MACD Line'],name='MACD Line',marker_color='black'),row=ROW,col=1)
            fig2.add_trace(go.Scatter(x=data_df.index,mode='lines',y=data_df['MACD Signal Line'],name='MACD Signal Line',marker_color='orange'),row=ROW,col=1)
    st.plotly_chart(fig2, use_container_width=True)
    st.write("***RAW DATA***")
    data_df


####################### Backtesting ####################################

if (ANALYSIS=='Strategy Backtest'):
    from datetime import datetime
    import backtrader as bt
    from strategies import *

    
    

    YESTERDAY=date.today()-timedelta(days=1)
    DEFAULT_START=YESTERDAY - timedelta(days=365)
    
    st.sidebar.markdown("***Get Historic Data***")
    START = st.sidebar.date_input("From", value=DEFAULT_START, max_value=YESTERDAY - timedelta(days=1))
    END = st.sidebar.date_input("Until", value=YESTERDAY, max_value=YESTERDAY, min_value=START)


    
    if st.checkbox('SMA STRATEGY'):
        cerebro = bt.Cerebro()  # create a "Cerebro" engine instance
        SMA_SMALL_WINDOW=st.number_input('SMA Small Window',min_value=2,max_value=200,value=10,step=1)
       
        SMA_BIG_WINDOW=st.number_input('SMA Big Window',min_value=5,max_value=500,value=30,step=1)
        
        st.write('When the Small Window or fast Moving Average')
        if st.button("Run SMA STRATEGY"):
            # Create a data feed
            data = bt.feeds.PandasData(dataname=yf.download(TICKER, START, END))

            cerebro.adddata(data)  # Add the data feed
            cerebro.addstrategy(SmaCross,pfast=SMA_SMALL_WINDOW,pslow=SMA_BIG_WINDOW)  # Add the trading strategy
            cerebro.run()  # run it all
            cerebro.plot()  # and plot it with a single command

    if st.checkbox ('RSI STRATEGY'):
        cerebro = bt.Cerebro()  # create a "Cerebro" engine instance
        OVERBOUGHT=st.number_input('Overbought Condition',min_value=1,max_value=100,value=70,step=1)
        OVERSOLD=st.number_input('Oversold Condtion',min_value=1,max_value=100,value=30,step=1)
        PERIOD =st.number_input('Period',min_value=2, max_value=100,value=21,step=1)
        st.write('When the Small Window or fast Moving Average')
        if st.button("Run RSI STRATEGY"):
            # Create a data feed
            data = bt.feeds.PandasData(dataname=yf.download(TICKER, START, END))

            cerebro.adddata(data)  # Add the data feed
            cerebro.addstrategy(RSIStrat,ovb=OVERBOUGHT,ovs=OVERSOLD,prd=PERIOD)  # Add the trading strategy
            cerebro.run()  # run it all
            cerebro.plot()  # and plot it with a single command
    
    if st.checkbox('Bollinger Bands Strategy'):
        if st.button('Run BBANDS Strategy'):
            cerebro = bt.Cerebro()
            data = bt.feeds.PandasData(dataname=yf.download(TICKER, START, END))
            cerebro.addsizer(bt.sizers.SizerFix)
            cerebro.adddata(data)
            cerebro.addstrategy(BBANDStrat)
            cerebro.run()
            cerebro.plot()
        

    if st.checkbox('Buy the Dip Strategy'):

            if st.button("Run Strategy"):
                cerebro = bt.Cerebro()
                data = bt.feeds.PandasData(dataname=yf.download(TICKER, START, END))
                cerebro.adddata(data)
                cerebro.addstrategy(ByTheDipStrategy)
                cerebro.run()
                cerebro.plot()
    if st.checkbox ("Candlestick Strategy"):
        f = pd.DataFrame()

        df = yf.download(TICKER,start=START , end=END)
        candle_df= df.ta.cdl_pattern(name='all')
        
        for col in candle_df.columns:
            if (candle_df[col]==0).all():
                candle_df.drop(col,axis=1,inplace=True)
        candlist=candle_df.columns.to_list() 
        st.write()
        col1,col2,col3 =st.columns(3)
        df["cundlesingal"]=0
        with col1:
            st.write('Cumulative Candlestick Strategy Considers all the found candlestick patterns')
            if st.button("Run Cumulative Strategy"):
                try:
                    candle_df.drop('CDL_INSIDE',axis=1,inplace=True)
                except KeyError as e:
                    print(f'No {e} found ')
                df["cundlesingal"]= candle_df.sum(axis=1)
                cerebro = bt.Cerebro()
                df.index.name = 'datetime'
                bt_data = SignalData(dataname=df)
                cerebro.adddata(bt_data)
                cerebro.addstrategy(CandleStrategy)
                cerebro.run()
                cerebro.plot(style='candlestick')
        with col2:
            st.write('Choose Specific Candlestick Strategy/ies')
            CANDLE_MUTLISELECT=st.multiselect('Add Candlestick Pattern',candlist)
            if st.button("Run Strategy with Chosen Candlestick Patterns"):
                for candle in CANDLE_MUTLISELECT:
                    df["cundlesingal"] += candle_df[candle]
                cerebro = bt.Cerebro()
                df.index.name = 'datetime'
                bt_data = SignalData(dataname=df)
                cerebro.adddata(bt_data)
                cerebro.addstrategy(CandleStrategy)
                cerebro.run()
                cerebro.plot(style='candlestick')
     
        with col3:
            st.write('Inside Candlestick Strategy Considers only the Inside Pattern')
            if st.button ('Run Inside Strategy'):
                df['cundlesingal']=candle_df['CDL_INSIDE']
                cerebro = bt.Cerebro()
                df.index.name = 'datetime'
                bt_data = SignalData(dataname=df)
                cerebro.adddata(bt_data)
                cerebro.addstrategy(CandleStrategy)
                cerebro.run()
                cerebro.plot(style='candlestick')


        st.write('**The folowing candlestick pattern were found**')
        st.write(candlist)          

        

      