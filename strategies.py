import backtrader as bt
import pandas_ta as pta
import backtrader.feeds as btfeeds
import datetime as dt
from backtrader.feeds import PandasData

    # Create a subclass of Strategy to define the indicators and logic

class ByTheDipStrategy(bt.Strategy):
    def __init__ (self):
        self.dataclose = self.datas[0].close
        self.order = None
    
    def notify_order(self,order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('Buy Excuted @ {}'.format(order.executed.price))
            elif order.issell():
                self.log('Sell Excuted @ {}'.format(order.executed.price))
            
            self.bar_executed = len(self)
        elif order.status in [order.Cancelled,order.Margin,order.Rejected]:
            self.log("Order Cancelled")
        self.order = None

    def next(self):
        self.log("Close {}".format(self.dataclose[0]))
        if self.order:
            return
        if not self.position:
            if self.dataclose[0]<self.dataclose[-1]:
                if self.dataclose[-1]<self.dataclose[-2]:
                    if self.dataclose[-3]<self.dataclose[-2]:
                        self.log('Buy Create {}'.format(self.dataclose[0]))
                        self.order = self.buy()
        else:        
            if self.dataclose[0]>self.dataclose[-1] :
                if self.dataclose[-1]>self.dataclose[-2]:
                    if self.data[-2]>self.data[-3]:
                        if self.data[-3]>self.data[-4]:
                            self.log('Sell Create {}'.format(self.dataclose[0]))
                            self.order=self.close()
                        
                        

    def log(self, txt):
        dt= self.datas[0].datetime.date(0)
        print("{} {}".format(dt.isoformat(),txt))


    
class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )
    
    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position


class RSIStrat(bt.Strategy):
    params= dict(
        ovs = 30,
        ovb = 70,
        prd = 21
    )
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.prd)
        

    def next(self):
        if not self.position:
            if self.rsi < self.p.ovs:
                self.buy()
        else:
            if self.rsi > self.p.ovb:
                self.close()



class BBANDStrat(bt.Strategy):

    '''
    This is a simple mean reversion bollinger band strategy.

    Entry Critria:
        - Long:
            - Price closes below the lower band
            - Stop Order entry when price crosses back above the lower band
        - Short:
            - Price closes above the upper band
            - Stop order entry when price crosses back below the upper band
    Exit Critria
        - Long/Short: Price touching the median line
    '''

    params = (
        ("period", 20),
        ("devfactor", 2),
        ("size", 20),
        ("debug", False),
        ('size',5)
        )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(period=self.p.period, devfactor=self.p.devfactor)
        self.sx = bt.indicators.CrossDown(self.data.close, self.boll.lines.top)
        self.lx = bt.indicators.CrossUp(self.data.close, self.boll.lines.bot)

    def next(self):

        orders = self.broker.get_orders_open()

        # Cancel open orders so we can track the median line
        if orders:
            for order in orders:
                self.broker.cancel(order)
        
        if not self.position:
            if self.data.close < self.boll.lines.bot:
                self.buy()
        else:
            if self.data.close > self.boll.lines.top:
                self.close()


        if self.p.debug:
            print('---------------------------- NEXT ----------------------------------')
            print("1: Data Name:                            {}".format(data._name))
            print("2: Bar Num:                              {}".format(len(data)))
            print("3: Current date:                         {}".format(data.datetime.datetime()))
            print('4: Open:                                 {}'.format(data.open[0]))
            print('5: High:                                 {}'.format(data.high[0]))
            print('6: Low:                                  {}'.format(data.low[0]))
            print('7: Close:                                {}'.format(data.close[0]))
            print('8: Volume:                               {}'.format(data.volume[0]))
            print('9: Position Size:                       {}'.format(self.position.size))
            print('--------------------------------------------------------------------')

    def notify_trade(self,trade):
        if trade.isclosed:
            dt = self.data.datetime.date()

            print('---------------------------- TRADE ---------------------------------')
            print("1: Data Name:                            {}".format(trade.data._name))
            print("2: Bar Num:                              {}".format(len(trade.data)))
            print("3: Current date:                         {}".format(dt))
            print('4: Status:                               Trade Complete')
            print('5: Ref:                                  {}'.format(trade.ref))
            print('6: PnL:                                  {}'.format(round(trade.pnl,2)))
            print('--------------------------------------------------------------------')



OHLCV = ['open', 'high', 'low', 'close', 'volume']

class SignalData(PandasData):
    """
    Define pandas DataFrame structure
    """
    cols = OHLCV + ['cundlesingal']
    # create lines
    lines = tuple(cols)
    # define parameters
    params = {c: -1 for c in cols}
    params.update({'datetime': None})
    params = tuple(params.items())

class CandleStrategy(bt.Strategy):

    def __init__(self):
        self.line= self.datas[0].cundlesingal
    
    def next(self):
        if not self.position:  # not in the market
            if self.line > 0:  # if you get an buy singal from the candlestick patern
                self.buy()  # enter long
            # if self.line < 0:
            #     self.close()
        else:
            if self.line < 0:  # in the market & cross to the downside
                self.close()  # close long position