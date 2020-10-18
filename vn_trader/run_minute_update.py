# flake8: noqa

import pandas as pd
import json
from datetime import datetime, timedelta
import numpy as np
import os
import pickle
from vnpy.trader.constant import Direction, Exchange, Interval
from vnpy.trader.object import HistoryRequest, SubscribeRequest
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.event import EventEngine
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




def load_history():
    """"""
    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(BinancesGateway)

    setting = {
        "key": "bEZCKVAkJYugYErdlg5GAj7PGgh72ieFIVtDVYgUwJuE7M0vLFM7lN7JuQPYB0AL",
        "secret": "LGZXmPUe4iXqOWlmjiUHGvf7XsdLSBWe5HfXauJoxu8qR9RTeZMUqzTOhcRiAK9K",
        "会话数": 3,
        "服务器": "REAL",
        "合约模式": "正向",
        "代理地址": "",
        "代理端口": 0}
    engine_name = 'BINANCES'
    main_engine.connect(setting, engine_name)

    yearlists = {'2020':'2021'}
    # all existed currency futures
    SYMBOLS = ['YFIIUSDT', 'SUSHIUSDT', 'UNIUSDT', 'TRBUSDT']
    symbols = SYMBOLS

    INTERV = 'MINUTE'
    # INTERV = 'YEAR'
    for symbol in symbols:
        this_directory = 'C:\\Workspace\\crypto\\data\\' + symbol
        this_model_file = this_directory + '\\' + symbol + '_FUTURES'+ '_5' + INTERV + '_all.pkl'
        if os.path.exists(this_model_file):

            print('load {} from existed file finished '.format(symbol))
            with open(this_model_file, 'rb') as f:
                olddata = pickle.load(f)
                f.close()

            startdate = pd.Timestamp.now() - timedelta(days=2)
            enddate = pd.Timestamp.now() + timedelta(days=1)
            quote = HistoryRequest(symbol, BinancesGateway.exchanges[0], start=startdate, end=enddate,
                                   interval=Interval.MINUTE)

            df_new = main_engine.query_history(quote, engine_name)

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
            print(2)

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

            print(2)
        else:
            raise Exception('old data not existed for ---{}'.format(symbol))


if __name__ == "__main__":
    load_history()