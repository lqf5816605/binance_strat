# flake8: noqa
from vnpy.event import EventEngine
import pandas as pd
import json
import os
import pickle
import numpy as np
from vnpy.trader.constant import Direction, Exchange, Interval
from vnpy.trader.object import HistoryRequest, SubscribeRequest, OrderRequest
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

# from vnpy.gateway.binance import BinanceGateway
from vnpy.gateway.binances import BinancesGateway
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
from vnpy.gateway.mt5 import Mt5Gateway

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

PATH = 'C:\\Workspace\\crypto\\data\\'
INTERV = 'MINUTE' #HOUR
YEARLISTS = [2020]
SYMBOLS = ['TRBUSDT']

def main():
    """"""
    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(BinancesGateway)
    engine_name = 'BINANCES'
    setting = {
        "key": "bEZCKVAkJYugYErdlg5GAj7PGgh72ieFIVtDVYgUwJuE7M0vLFM7lN7JuQPYB0AL",
        "secret": "LGZXmPUe4iXqOWlmjiUHGvf7XsdLSBWe5HfXauJoxu8qR9RTeZMUqzTOhcRiAK9K",
        "会话数": 3,
        "服务器": "REAL",
        "合约模式": "正向",
        "代理地址": "",
        "代理端口": 0}
    main_engine.connect(setting, engine_name)

    yearlists = {'2020':'2021'}
    # all existed currency futures
    symbols = SYMBOLS

    # symbol = symbols[0]
    # quote = SubscribeRequest(symbol, BinanceGateway.exchanges[0])
    # df = main_engine.subscribe(quote,'BINANCE')
    INTERV = 'MINUTE'
    # INTERV = 'YEAR'
    for symbol in symbols:
        this_directory = 'C:\\Workspace\\crypto\\data\\' + symbol
        if not os.path.exists(this_directory):
            os.makedirs(this_directory)
        for key, var in yearlists.items():
            startdate = pd.to_datetime(key + '-01-01')
            enddate = pd.to_datetime(var + '-01-06')
            print('query {} minute history '.format(symbol))
            quote = HistoryRequest(symbol, BinancesGateway.exchanges[0], start=startdate, end=enddate, interval=Interval.MINUTE)

            df = main_engine.query_history(quote, engine_name)
            # HOUR
            this_model_file = this_directory + '\\' + symbol + '_FUTURES' + '_' + INTERV + '_' + key + '.pkl'
            # MINUTE
            # this_model_file = this_directory + '\\' + symbol + '_' + INTERV + '_all' + '.pkl'
            with open(this_model_file, 'wb') as f:
                # first save model
                pickle.dump(df, f)


def min_data(symbol, year):
    this_model_file = PATH + symbol + '\\' + symbol + '_FUTURES' + '_' + INTERV + '_' + str(year) + '.pkl'
    newpath = PATH + symbol + '\\' + symbol + '_FUTURES' + '_' + INTERV + '_' + str(year) + '_data.pkl'
    with open(this_model_file, 'rb') as f:
        data = pickle.load(f)
        f.close()

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

    df.to_pickle(newpath)

def switch_5_data(symbol, year):

    data = pd.read_pickle(
            'C:\\Workspace\\crypto\\data\\' + symbol + '\\' + symbol + '_FUTURES' + '_' + INTERV + '_' + str(year) + '_data.pkl')
    data.index = pd.to_datetime(data['datetime'])

    df_volume = data['volume'].resample('5min', how=np.sum)
    df_open = data['open'].resample('5min', how='first')
    df_high = data['high'].resample('5min', how=np.max)
    df_low = data['low'].resample('5min', how=np.min)
    df_close = data['close'].resample('5min', how='last')
    df_datetime = data['datetime'].resample('5min', how='first')
    print(2)

    df = {'datetime': df_datetime,
          'open': df_open,
          'high': df_high,
          'low': df_low,
          'close': df_close,
          'volume': df_volume,
          }

    df = pd.DataFrame(df)

    # df.to_pickle(newpath)
    df.to_pickle('C:\\Workspace\\crypto\\data\\' + symbol + '\\' + symbol + '_FUTURES' + '_5' + INTERV + '_all.pkl')

if __name__ == "__main__":

    main()

    symbols = SYMBOLS
    for symbol in symbols:
        min_data(symbol,2020)
        switch_5_data(symbol,2020)

