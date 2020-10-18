from vnpy.event import EventEngine
import pandas as pd
from datetime import timedelta
import json
import os
import pickle
import numpy as np
import time
from vnpy.trader.object import HistoryRequest, SubscribeRequest, OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, Exchange, Interval, OrderType, Offset
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from datetime import datetime
# from vnpy.gateway.binance import BinanceGateway
from vnpy.gateway.binances import BinancesGateway
from examples.vn_trader.strategies_wiki import strat_ma_cross, strat_breakout_volume, strat_needle, strat_many_bars, strat_breakout_three_doji, strat_pullback
from examples.vn_trader.params import param_load
from examples.vn_trader.file_send import send_wechat
import logging
import warnings
warnings.filterwarnings('ignore')
# from vnpy.gateway.bitmex import BitmexGateway
# from vnpy.gateway.futu import FutuGateway
# from vnpy.gateway.ib import IbGateway
# from vnpy.gateway.ctp import CtpGateway
# from vnpy.gateway.ctptest import CtptestGateway
# from vnpy.gateway.mini import MiniGateway
# from vnpy.gateway.sopt import SoptGateway
# from vnpy.gateway.minitest import MinitestGateway
# from vnpy.gateway.femas import FemasGateway
# from vnpy.gateway.tiger import TigerGateway
# from vnpy.gateway.oes import OesGateway
# from vnpy.gateway.okex import OkexGateway
# from vnpy.gateway.huobi import HuobiGateway
# from vnpy.gateway.bitfinex import BitfinexGateway
# from vnpy.gateway.onetoken import OnetokenGateway
# from vnpy.gateway.okexf import OkexfGateway
# from vnpy.gateway.okexs import OkexsGateway
# from vnpy.gateway.xtp import XtpGateway
# from vnpy.gateway.huobif import HuobifGateway
# from vnpy.gateway.tap import TapGateway
# from vnpy.gateway.tora import ToraGateway
# from vnpy.gateway.alpaca import AlpacaGateway
# from vnpy.gateway.da import DaGateway
# from vnpy.gateway.coinbase import CoinbaseGateway
# from vnpy.gateway.bitstamp import BitstampGateway
# from vnpy.gateway.gateios import GateiosGateway
# from vnpy.gateway.bybit import BybitGateway
# from vnpy.gateway.deribit import DeribitGateway
# from vnpy.gateway.uft import UftGateway
# from vnpy.gateway.okexo import OkexoGateway

# from vnpy.gateway.mt4 import Mt4Gateway
# from vnpy.gateway.mt5 import Mt5Gateway

# from vnpy.app.cta_strategy import CtaStrategyApp
# from vnpy.app.csv_loader import CsvLoaderApp
# from vnpy.app.algo_trading import AlgoTradingApp
# from vnpy.app.cta_backtester import CtaBacktesterApp
# from vnpy.app.data_recorder import DataRecorderApp
# from vnpy.app.risk_manager import RiskManagerApp
# from vnpy.app.script_trader import ScriptTraderApp
# from vnpy.app.rpc_service import RpcServiceApp
# from vnpy.app.spread_trading import SpreadTradingApp
# from vnpy.app.portfolio_manager import PortfolioManagerApp
# from vnpy.app.option_master import OptionMasterApp
# from vnpy.app.chart_wizard import ChartWizardApp
# from vnpy.app.excel_rtd import ExcelRtdApp
# from vnpy.app.data_manager import DataManagerApp
# from vnpy.app.portfolio_strategy import PortfolioStrategyApp


PATH = 'C:\\ProgramData\\Crypto\\data\\'
STRAT_IDS = ['needle','ma_cross', 'breakout_volume','breakout_three_doji','pullback']
SYMBOLS = ['YFIIUSDT', 'SUSHIUSDT', 'UNIUSDT','TRBUSDT', 'WAVESUSDT']
PCT = 8


class StratRecord:
    symbol: str
    strat_id: None
    order_id: None
    position = 0
    trade = 0
    openprice = 0.0
    volume = 0
    time : str

    def __init__(self, symbol, strat_id):
        self.symbol = symbol
        self.strat_id = strat_id
        self.position = 0
        self.volume = 0


class DataQuote:
    symbol: str
    last: float
    bid_price_1: float
    ask_price_1: float
    bid_price_5: float
    ask_price_5: float
    min_volume: float

    def __init__(self, symbol):
        self.symbol = symbol


class BinanceStrat(object):

    def __init__(self):

        self.main_engine = None
        self.enginename = 'BINANCES'
        self.symbols = SYMBOLS
        self.cash_avail = 0
        self.data_hist = {}
        self.data_quote = {}
        self.strat_class = {}
        self.params = param_load()
        self.trade_record = pd.DataFrame({})
        self.trade_record = pd.read_csv(PATH + '\\save_strategy\\trade_record.csv')
        for symbol in self.symbols:
            self.data_quote[symbol] = DataQuote(symbol)
            self.strat_class[symbol] = {}
            for strat_id in STRAT_IDS:
                self.strat_class[symbol][strat_id] = StratRecord(symbol, strat_id)
                hist_records = self.trade_record[(self.trade_record['symbol'] == symbol) & (self.trade_record['strat_id'] == strat_id)]
                if len(hist_records) == 0:
                    continue
                else:
                    self.strat_class[symbol][strat_id].strat_id = hist_records['strat_id'].iloc[-1]
                    self.strat_class[symbol][strat_id].position = hist_records['position'].iloc[-1]
                    self.strat_class[symbol][strat_id].openprice = hist_records['price'].iloc[-1]
                    self.strat_class[symbol][strat_id].volume = hist_records['volume'].iloc[-1]
                    self.strat_class[symbol][strat_id].time = hist_records['time'].iloc[-1]

        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('strategy.log')
        fh.setLevel(logging.DEBUG)
        # set formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add handler to logger
        self.logger.addHandler(fh)
        self.logger.info('this new test strategy -- learning timing ----')

    def initiate(self):

        # first load history

        qapp = create_qapp()

        event_engine = EventEngine()

        self.main_engine = MainEngine(event_engine)

        self.main_engine.add_gateway(BinancesGateway)

        setting = {
            "key": "bEZCKVAkJYugYErdlg5GAj7PGgh72ieFIVtDVYgUwJuE7M0vLFM7lN7JuQPYB0AL",
            "secret": "LGZXmPUe4iXqOWlmjiUHGvf7XsdLSBWe5HfXauJoxu8qR9RTeZMUqzTOhcRiAK9K",
            "会话数": 3,
            "服务器": "REAL",
            "合约模式": "正向",
            "代理地址": "",
            "代理端口": 0}
        enginename = 'BINANCES'

        self.main_engine.connect(setting, self.enginename)
        time.sleep(3)
        # cash_available = self.main_engine.engines['oms'].accounts['BINANCES.USDT'].available
        # print(' cash available {}'.format(cash_available))
        self.load_history()
        for symbol in self.symbols:
            self.data_quote[symbol].min_volume = self.main_engine.engines['oms'].contracts[symbol + '.BINANCE'].min_volume

        self.subscribe_quote()
        time.sleep(2)
        self.cancel_all_pendings()

    def cal_cash(self):

        cash_available = self.main_engine.engines['oms'].accounts['BINANCES.USDT'].available
        self.cash_avail = cash_available

    def subscribe_quote(self):

        for symbol in self.symbols:
            this_directory = PATH + symbol
            this_model_file = this_directory + '\\' + symbol + '_FUTURES' + '_5MINUTE_all.pkl'

            try:
                self.data_hist[symbol] = pd.read_pickle(this_model_file)
            except Exception as e:
                print('No data found error')

        for symbol in self.symbols:
            quote = SubscribeRequest(symbol, BinancesGateway.exchanges[0])
            self.main_engine.subscribe(quote, self.enginename)

    def main_logic(self):

        while True:

            prev_time = pd.Timestamp.now()
            time.sleep(10)
            print('------------------------------------')
            self.cal_cash()

            for symbol in self.symbols:

                x = self.main_engine.engines['oms'].ticks
                info = symbol + "." + 'BINANCE'
                if info not in list(x.keys()):
                    print('no data, resubscribe')
                    quote = SubscribeRequest(symbol, BinancesGateway.exchanges[0])
                    self.main_engine.subscribe(quote, self.enginename)

                else:
                    x = x[info]
                    this_symbol_data = self.data_quote[symbol]
                    this_symbol_data.last = x.last_price
                    this_symbol_data.bid_price_1 = x.bid_price_1
                    this_symbol_data.ask_price_1 = x.ask_price_1
                    this_symbol_data.bid_price_5 = x.bid_price_5
                    this_symbol_data.ask_price_5 = x.ask_price_5
                # strategy
                self.order_logic(symbol)

                # update 5 min bar
                curtime = pd.Timestamp.now()

                # if symbol == 'YFIIUSDT':
                #   self.order_test(symbol)
                # algo logic when bar updated
                # curtime.minute % 5 == 0
                if curtime.minute % 1 == 0 and curtime.minute > prev_time.minute:

                    t1 = time.time()
                    hist_min = pd.Timestamp.now() - timedelta(minutes=20)
                    df = None
                    while df is None:
                        try:
                            quote = HistoryRequest(symbol, self.main_engine.gateways[self.enginename].exchanges[0],
                                                   start=datetime(hist_min.year, hist_min.month, hist_min.day,
                                                                  hist_min.hour, 0, 0), interval=Interval.MINUTE)

                            df = self.main_engine.query_history(quote, self.enginename)
                        except:
                            time.sleep(20)
                            print('---------------reloading------------------')
                    df_new, df_5min = self.get_5min_data(df)
                    t2 = time.time()
                    # print(t2 - t1)
                    olddata = self.data_hist[symbol]
                    newdate = df_5min['datetime'].iloc[0]
                    olddata = olddata[olddata['datetime'] < newdate]
                    newdata = olddata.append(df_5min.iloc[:-1])
                    newdata.drop_duplicates(inplace=True)
                    self.data_hist[symbol] = newdata[['datetime','open','high', 'low', 'close', 'volume']]

                    this_directory = PATH + symbol
                    this_model_file = this_directory + '\\' + symbol + '_FUTURES' + '_5MINUTE_all.pkl'
                    with open(this_model_file, 'wb') as f:
                        # second save training names
                        pickle.dump(self.data_hist[symbol], f)
                        f.close()

    def cancel_all_pendings(self):

        if len(self.main_engine.get_all_orders()) == 0:
            return
        else:
            for thisorder in self.main_engine.get_all_orders():
                if thisorder.status.value in ['部分成交', '未成交']:
                    try:
                        cancelorder = CancelRequest(symbol=thisorder.symbol, orderid=thisorder.vt_orderid.split('.')[1],
                                                exchange=self.main_engine.gateways[self.enginename].exchanges[0])
                        self.main_engine.cancel_order(cancelorder, self.enginename)
                    except:
                        pass

        if len(self.main_engine.engines['oms'].active_orders) == 0:
            return
        else:
            for thisorder in self.main_engine.engines['oms'].active_orders:
                try:
                    cancelorder = CancelRequest(symbol=thisorder.symbol, orderid=thisorder.vt_orderid.split('.')[1],
                                            exchange=self.main_engine.gateways[self.enginename].exchanges[0])
                    self.main_engine.cancel_order(cancelorder, self.enginename)
                except:
                    pass
        pass

    def order_test(self, symbol):
        volume = (self.cash_avail * 20.0 / 20) / self.data_quote[symbol].ask_price_1
        if self.data_quote[symbol].min_volume == 1:
            volume = int(volume) * 1.0
        else:
            len_volume = len(str(self.data_quote[symbol].min_volume).split(".")[1])
            volume = round(volume, len_volume)

        thisorder = OrderRequest(symbol=symbol, exchange=self.main_engine.gateways[self.enginename].exchanges[0],
                                 direction=Direction.LONG, type=OrderType.LIMIT,
                                 price=self.data_quote[symbol].bid_price_5,
                                 volume=volume, offset=Offset.OPEN)

        this_order_id = self.main_engine.send_order(thisorder, self.enginename)
        return this_order_id

    def order_logic(self, symbol):

        for strat_id in STRAT_IDS:
            this_strat_data = self.strat_class[symbol][strat_id]
            this_signal = 0
            if strat_id == 'ma_cross':
                this_signal, msg = strat_ma_cross(self.data_hist[symbol], self.data_quote[symbol], self.params[symbol][strat_id])
                # print(strat_id + '---' + msg)
            elif strat_id == 'breakout_volume':
                this_signal, msg = strat_breakout_volume(self.data_hist[symbol], self.data_quote[symbol],self.params[symbol][strat_id])
                # print(strat_id + '---' + msg)
            elif strat_id == 'needle':
                this_signal, msg = strat_needle(self.data_hist[symbol], self.data_quote[symbol],
                                                         self.params[symbol][strat_id])
                # print(strat_id + '---' + msg)
            elif strat_id == 'many_bars':
                this_signal, msg = strat_many_bars(self.data_hist[symbol], self.data_quote[symbol],
                                                self.params[symbol][strat_id])
                # print(strat_id + '---' + msg)
            elif strat_id == 'breakout_three_doji':
                this_signal, msg = strat_breakout_three_doji(self.data_hist[symbol], self.data_quote[symbol],
                                                   self.params[symbol][strat_id])

            elif strat_id == 'pullback':
                this_signal, msg = strat_pullback(self.data_hist[symbol], self.data_quote[symbol],
                                                             self.params[symbol][strat_id])
                # print(strat_id + '---' + msg)
            # if currently have no positions
            if this_strat_data.position == 0:

                if this_signal == 1:
                    # first 20.0 is leverage, second 20 is how much percent
                    volume = (self.cash_avail*20.0/PCT)/self.data_quote[symbol].ask_price_1
                    if self.data_quote[symbol].min_volume == 1:
                        volume = int(volume) * 1.0
                    else:
                        len_volume = len(str(self.data_quote[symbol].min_volume).split(".")[1])
                        volume = round(volume, len_volume)

                    thisorder = OrderRequest(symbol=symbol, exchange=self.main_engine.gateways[self.enginename].exchanges[0],
                                             direction=Direction.LONG, type=OrderType.LIMIT, price=self.data_quote[symbol].ask_price_5,
                                             volume=volume, offset=Offset.OPEN)

                    this_order_id = self.main_engine.send_order(thisorder, self.enginename)
                    this_strat_data.strat_id = strat_id
                    this_strat_data.order_id = this_order_id
                    this_strat_data.openprice = self.data_quote[symbol].ask_price_1
                    this_strat_data.volume = volume
                    this_strat_data.trade = 1
                    this_strat_data.position = 1
                    this_strat_data.time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.logger.info('strat_id {} -- symbol {}  open long position'.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  open long position'.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  open long position'.format(strat_id, symbol))
                    self.trade_record = self.trade_record.append(
                        pd.DataFrame(
                            {'strat_id': [strat_id], 'symbol': [symbol], 'position': [this_strat_data.position],
                             'trade': [this_strat_data.trade], 'price': [this_strat_data.openprice], 'volume': [
                                this_strat_data.volume], 'order_id': [this_strat_data.order_id],
                             'time': [this_strat_data.time]}))
                    self.trade_record.to_csv(PATH + '\\save_strategy\\trade_record.csv', index=None)
                    # send order

                if this_signal == -1:
                    volume = (self.cash_avail*20.0/PCT)/self.data_quote[symbol].bid_price_1
                    if self.data_quote[symbol].min_volume == 1:
                        volume = int(volume)
                    else:
                        len_volume = len(str(self.data_quote[symbol].min_volume).split(".")[1])
                        volume = round(volume, len_volume)

                    thisorder = OrderRequest(symbol=symbol, exchange=self.main_engine.gateways[self.enginename].exchanges[0],
                                             direction=Direction.SHORT, type=OrderType.LIMIT, price=self.data_quote[symbol].bid_price_5,
                                             volume=volume, offset=Offset.OPEN)

                    this_order_id = self.main_engine.send_order(thisorder, self.enginename)
                    this_strat_data.strat_id = strat_id
                    this_strat_data.order_id = this_order_id
                    this_strat_data.openprice = self.data_quote[symbol].bid_price_1
                    this_strat_data.volume = volume
                    this_strat_data.trade = -1
                    this_strat_data.position = -1
                    this_strat_data.time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.logger.info('strat_id {} -- symbol {}  open short position'.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  open short position'.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  open short position'.format(strat_id, symbol))
                    self.trade_record = self.trade_record.append(
                        pd.DataFrame(
                            {'strat_id': [strat_id], 'symbol': [symbol], 'position': [this_strat_data.position],
                             'trade': [this_strat_data.trade], 'price': [this_strat_data.openprice], 'volume': [
                                this_strat_data.volume], 'order_id': [this_strat_data.order_id],
                             'time': [this_strat_data.time]}))
                    self.trade_record.to_csv(PATH + '\\save_strategy\\trade_record.csv', index=None)
                    # send order

            elif this_strat_data.position == 1:
                try:
                    cur_price = self.data_quote[symbol].bid_price_1
                except:
                    pass
                pass_time = pd.Timestamp.now() - pd.to_datetime(this_strat_data.time)
                pass_time = pass_time.seconds
                print('current strat_id {} symbol {} position is {}, time passed {}'.format(strat_id, symbol,
                                                                                            this_strat_data.position,
                                                                                            pass_time))
                bool_exit = False
                # stop loss
                if cur_price < this_strat_data.openprice * (1 - 0.008):

                    bool_exit = True
                    self.logger.info('strat_id {} -- symbol {}  stop loss '.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  stop loss '.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  stop loss '.format(strat_id, symbol))
                # stop profit
                elif cur_price > this_strat_data.openprice * (1 + 0.025):
                    bool_exit = True
                    self.logger.info('strat_id {} -- symbol {}  stop profit '.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  stop profit '.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  stop profit '.format(strat_id, symbol))
                elif pass_time > 60 * self.params[symbol][strat_id]['buy']['interval']*5:
                    bool_exit = True
                    self.logger.info('strat_id {} -- symbol {}  time decay '.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  time decay '.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  time decay '.format(strat_id, symbol))
                if bool_exit:

                    volume = this_strat_data.volume
                    print('{} price {}'.format(symbol,self.data_quote[symbol].bid_price_5))
                    thisorder = OrderRequest(symbol=symbol,
                                             exchange=self.main_engine.gateways[self.enginename].exchanges[0],
                                             direction=Direction.SHORT, type=OrderType.LIMIT,
                                             price=self.data_quote[symbol].bid_price_5, volume=volume, offset=Offset.CLOSE)

                    this_order_id = self.main_engine.send_order(thisorder, self.enginename)
                    this_strat_data.strat_id = strat_id
                    this_strat_data.order_id = this_order_id
                    this_strat_data.openprice = self.data_quote[symbol].bid_price_1
                    this_strat_data.volume = volume
                    this_strat_data.trade = -1
                    this_strat_data.position = 0
                    this_strat_data.time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

                    self.trade_record = self.trade_record.append(
                        pd.DataFrame(
                            {'strat_id': [strat_id], 'symbol': [symbol], 'position': [this_strat_data.position],
                             'trade': [this_strat_data.trade], 'price': [this_strat_data.openprice], 'volume': [
                                this_strat_data.volume], 'order_id': [this_strat_data.order_id],
                             'time': [this_strat_data.time]}))
                    self.trade_record.to_csv(PATH + '\\save_strategy\\trade_record.csv', index=None)

            elif this_strat_data.position == -1:

                try:
                    cur_price = self.data_quote[symbol].ask_price_1
                except:
                    pass
                pass_time = pd.Timestamp.now() - pd.to_datetime(this_strat_data.time)
                pass_time = pass_time.seconds
                print('current strat_id {} symbol {} position is {}, time passed {}'.format(strat_id, symbol,
                                                                                            this_strat_data.position,
                                                                                            pass_time))
                bool_exit = False
                # stop loss
                if cur_price > this_strat_data.openprice * (1 + 0.008):

                    bool_exit = True
                    self.logger.info('strat_id {} -- symbol {}  stop loss '.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  stop loss '.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  stop loss '.format(strat_id, symbol))
                # stop profit
                elif cur_price < this_strat_data.openprice * (1 - 0.025):
                    bool_exit = True
                    self.logger.info('strat_id {} -- symbol {}  stop profit '.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  stop profit '.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  stop profit '.format(strat_id, symbol))
                elif pass_time > 60 * self.params[symbol][strat_id]['sell']['interval']*5:
                    bool_exit = True
                    self.logger.info('strat_id {} -- symbol {}  time decay '.format(strat_id, symbol))
                    print('strat_id {} -- symbol {}  time decay '.format(strat_id, symbol))
                    send_wechat('strat_id {} -- symbol {}  time decay '.format(strat_id, symbol))

                if bool_exit:
                    volume = this_strat_data.volume
                    print('{} price {}'.format(symbol, self.data_quote[symbol].ask_price_5))
                    thisorder = OrderRequest(symbol=symbol,
                                             exchange=self.main_engine.gateways[self.enginename].exchanges[0],
                                             direction=Direction.LONG, type=OrderType.LIMIT,
                                             price=self.data_quote[symbol].ask_price_5, volume=volume, offset=Offset.CLOSE)

                    this_order_id = self.main_engine.send_order(thisorder, self.enginename)
                    this_strat_data.strat_id = strat_id
                    this_strat_data.order_id = this_order_id
                    this_strat_data.openprice = self.data_quote[symbol].ask_price_1
                    this_strat_data.volume = volume
                    this_strat_data.trade = 1
                    this_strat_data.position = 0
                    this_strat_data.time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

                    self.trade_record = self.trade_record.append(
                        pd.DataFrame(
                            {'strat_id': [strat_id], 'symbol': [symbol], 'position': [this_strat_data.position],
                             'trade': [this_strat_data.trade], 'price': [this_strat_data.openprice], 'volume': [
                                this_strat_data.volume], 'order_id': [this_strat_data.order_id],
                             'time': [this_strat_data.time]}))

                    self.trade_record.to_csv(PATH + 'save_strategy\\trade_record.csv', index=None)

    def get_5min_data(self, data):

        datelists = []
        closelists = []
        highlists = []
        openlists = []
        lowlists = []
        volumelists = []
        for curdata in data:
            datelists.append(pd.Timestamp(curdata.datetime).strftime('%Y-%m-%d %H:%M:%S'))
            openlists.append(curdata.open_price)
            highlists.append(curdata.high_price)
            lowlists.append(curdata.low_price)
            closelists.append(curdata.close_price)
            volumelists.append(curdata.volume)

        df = {'datetime': datelists,
              'open': openlists,
              'high': highlists,
              'low': lowlists,
              'close': closelists,
              'volume': volumelists,
              }
        df = pd.DataFrame(df)
        if len(data) != 0:
            df['NAME'] = data[0].symbol
        df.index = pd.to_datetime(df['datetime'])
        data = df.copy()

        df_volume = data['volume'].resample('5min', how=np.sum)
        df_open = data['open'].resample('5min', how='first')
        df_high = data['high'].resample('5min', how=np.max)
        df_low = data['low'].resample('5min', how=np.min)
        df_close = data['close'].resample('5min', how='last')
        df_datetime = data['datetime'].resample('5min', how='first')

        df_5min = {'datetime': df_datetime,
                   'open': df_open,
                   'high': df_high,
                   'low': df_low,
                   'close': df_close,
                   'volume': df_volume}

        df_5min = pd.DataFrame(df_5min)
        return df, df_5min

    def load_history(self):
        INTERV = 'MINUTE'
        for symbol in SYMBOLS:
            this_directory = PATH + symbol
            this_model_file = this_directory + '\\' + symbol + '_FUTURES' + '_5' + INTERV + '_all.pkl'
            if os.path.exists(this_model_file):

                print('load {} from existed file finished '.format(symbol))
                with open(this_model_file, 'rb') as f:
                    olddata = pickle.load(f)
                    f.close()

                startdate = pd.Timestamp.now() - timedelta(days=2)
                enddate = pd.Timestamp.now() + timedelta(days=1)
                df_new = None
                while df_new is None:

                    try:
                        quote = HistoryRequest(symbol, BinancesGateway.exchanges[0], start=startdate, end=enddate,
                                               interval=Interval.MINUTE)

                        df_new = self.main_engine.query_history(quote, self.enginename)
                    except:
                        time.sleep(10)
                        print('--------------------reloading--------------')

                print('Updating finished ! ')

                datelists = []
                closelists = []
                highlists = []
                openlists = []
                lowlists = []
                volumelists = []
                for curdata in df_new:
                    datelists.append(pd.Timestamp(curdata.datetime).strftime('%Y-%m-%d %H:%M:%S'))
                    openlists.append(curdata.open_price)
                    highlists.append(curdata.high_price)
                    lowlists.append(curdata.low_price)
                    closelists.append(curdata.close_price)
                    volumelists.append(curdata.volume)

                newdata = {'datetime': datelists,
                           'open': openlists,
                           'high': highlists,
                           'low': lowlists,
                           'close': closelists,
                           'volume': volumelists,
                           }
                newdata = pd.DataFrame(newdata)

                data = newdata.copy()
                newstart = data[data['datetime'].apply(lambda x: x[-8:]) == '00:00:00'].iloc[0]['datetime']
                data = data[data['datetime'] >= newstart]
                # 1min to 5min
                data.index = pd.to_datetime(data['datetime'])
                df_volume = data['volume'].resample('5min', how=np.sum)
                df_open = data['open'].resample('5min', how='first')
                df_high = data['high'].resample('5min', how=np.max)
                df_low = data['low'].resample('5min', how=np.min)
                df_close = data['close'].resample('5min', how='last')
                df_datetime = data['datetime'].resample('5min', how='first')


                df = {'datetime': df_datetime,
                      'open': df_open,
                      'high': df_high,
                      'low': df_low,
                      'close': df_close,
                      'volume': df_volume,
                      }

                df = pd.DataFrame(df)
                #

                newdate = df['datetime'].iloc[0]
                olddata = olddata[olddata['datetime'] < newdate]
                alldata = olddata.append(df.iloc[:-1])
                alldata.drop_duplicates(inplace=True)
                with open(this_model_file, 'wb') as f:
                    # second save training names
                    pickle.dump(alldata, f)
                    f.close()


            else:
                raise Exception('old data not existed for ---{}'.format(symbol))

if __name__ == "__main__":
    strat = BinanceStrat()
    strat.initiate()
    strat.main_logic()
