# flake8: noqa
from vnpy.event import EventEngine
import pandas as pd
import json
import os
import pickle
import time
from vnpy.trader.constant import Direction, Exchange, Interval
from vnpy.trader.object import HistoryRequest, SubscribeRequest, OrderRequest
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy.gateway.binance import BinanceGateway
# from vnpy.gateway.binances import BinancesGateway
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


def main():
    """"""
    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(BinanceGateway)

    setting = {
    "key": "pUJsE0fa62rpAEUo71P27kV6GUUA6fSlojhWodZ5kFjGQFPe2PSGt9Dn2eNE6aHf",
    "secret": "jMWC0Ld0YkCy1lEnupsU7YJMr3VPR8of9W80iGLOG816b2xarvnWUN8uyOEz3g5w",
    "session_number": 3,
    "server": ["REAL"],
    "proxy_host": "",
    "proxy_port": 0}
    main_engine.connect(setting, 'BINANCE')
    time.sleep(3)
    # main_engine.event_engine.register(EVENT_TIMER, self.process_timer_event)
    yearlists = {'2017':'2018',
                 '2018':'2019',
                 '2019':'2020',
                 '2020':'2021'}

    yearlists = {'2020':'2021'}
    # all existed currency futures
    symbols = ['SXPBTC','EOSBTC','ADABTC','BANDBTC','VETBTC','XTZBTC','BNBBTC','KAVABTC',
              'XLMBTC','ZECBTC','COMPBTC','KNCBTC','ATOMBTC','RLCBTC','NEOBTC','ALGOBTC','XMRBTC',
              'ONTBTC','THETABTC','IOSTBTC','ZILBTC','DASHBTC','OMGBTC','QTUMBTC','IOTABTC','BATBTC',
              'DOGEBTC','ZRXBTC']

    symbol = 'BTCUSDT'
    quote = HistoryRequest(symbol, BinanceGateway.exchanges[0], start=pd.to_datetime('2020-09-21'), end = pd.to_datetime('2020-09-22'), interval=Interval.HOUR)

    df = main_engine.query_history(quote, 'BINANCE')
    symbols = ['btcusdt','ethusdt']
    for symbol in symbols:
        quote = SubscribeRequest(symbol, BinanceGateway.exchanges[0])
        main_engine.subscribe(quote, 'BINANCE')

    while True:

        time.sleep(2)

        for symbol in symbols:
            # x = main_engine.get_gateway('BINANCE').market_ws_api.ticks
            x = main_engine.engines['oms'].ticks
            info = symbol + "." + 'BINANCE'
            if  info not in list(x.keys()):
                print('no data, resubscribe')
                quote = SubscribeRequest(symbol, BinanceGateway.exchanges[0])
                main_engine.subscribe(quote, 'BINANCE')

            else:
                x = x[info]

                print("-" * 30)
                print('{} --- {}  ask1 {}, bid1 {}, volume {}'.format(x.datetime.strftime('%Y-%m-%d %H:%M:%S'), x.name, x.ask_price_1, x.bid_price_1, x.volume))


    """
    symbols = ['LINKUSDT','WAVESUSDT' ]
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
            print('load {} from existed file finished '.format(symbol))
            quote = HistoryRequest(symbol, BinanceGateway.exchanges[0], start=startdate, end=enddate, interval=Interval.MINUTE)

            df = main_engine.query_history(quote, 'BINANCE')
            # HOUR
            this_model_file = this_directory + '\\' + symbol + '_' + INTERV + '_' + key + '.pkl'
            # MINUTE
            # this_model_file = this_directory + '\\' + symbol + '_' + INTERV + '_all' + '.pkl'
            with open(this_model_file, 'wb') as f:
                # first save model
                pickle.dump(df, f)
            print(2)
    #main_engine.send_order()
    """
    # main_engine.add_gateway(CtpGateway)
    # main_engine.add_gateway(CtptestGateway)
    # main_engine.add_gateway(MiniGateway)
    # main_engine.add_gateway(SoptGateway)
    # main_engine.add_gateway(MinitestGateway)
    # main_engine.add_gateway(FemasGateway)
    # main_engine.add_gateway(UftGateway)
    # main_engine.add_gateway(IbGateway)
    # main_engine.add_gateway(FutuGateway)
    # main_engine.add_gateway(BitmexGateway)
    # main_engine.add_gateway(TigerGateway)
    # main_engine.add_gateway(OesGateway)
    # main_engine.add_gateway(OkexGateway)
    # main_engine.add_gateway(HuobiGateway)
    # main_engine.add_gateway(BitfinexGateway)
    # main_engine.add_gateway(OnetokenGateway)
    # main_engine.add_gateway(OkexfGateway)
    # main_engine.add_gateway(HuobifGateway)
    # main_engine.add_gateway(XtpGateway)
    # main_engine.add_gateway(TapGateway)
    # main_engine.add_gateway(ToraGateway)
    # main_engine.add_gateway(AlpacaGateway)
    # main_engine.add_gateway(OkexsGateway)
    # main_engine.add_gateway(DaGateway)
    # main_engine.add_gateway(CoinbaseGateway)
    # main_engine.add_gateway(BitstampGateway)
    # main_engine.add_gateway(GateiosGateway)
    # main_engine.add_gateway(BybitGateway)
    # main_engine.add_gateway(DeribitGateway)
    # main_engine.add_gateway(OkexoGateway)
    # main_engine.add_gateway(BinancefGateway)
    # main_engine.add_gateway(Mt4Gateway)
    # main_engine.add_gateway(Mt5Gateway)

    # main_engine.add_app(CtaStrategyApp)
    # main_engine.add_app(CtaBacktesterApp)
    # main_engine.add_app(CsvLoaderApp)
    # main_engine.add_app(AlgoTradingApp)
    # main_engine.add_app(DataRecorderApp)
    # main_engine.add_app(RiskManagerApp)
    # main_engine.add_app(ScriptTraderApp)
    # main_engine.add_app(RpcServiceApp)
    # main_engine.add_app(SpreadTradingApp)
    # main_engine.add_app(PortfolioManagerApp)
    # main_engine.add_app(OptionMasterApp)
    # main_engine.add_app(ChartWizardApp)
    # main_engine.add_app(ExcelRtdApp)
    # main_engine.add_app(DataManagerApp)
    # main_engine.add_app(PortfolioStrategyApp)
    """
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()
    """
    pass

if __name__ == "__main__":
    main()