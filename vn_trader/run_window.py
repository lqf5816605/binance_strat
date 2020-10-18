# flake8: noqa
from vnpy.event import EventEngine
import pandas as pd
import json
import os
import pickle
from vnpy.trader.constant import Direction, Exchange, Interval, OrderType, Offset
from vnpy.trader.object import HistoryRequest, SubscribeRequest, OrderRequest
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
# from vnpy.gateway.ctptest import CtptestGateway
# from vnpy.gateway.ctp import CtpGateway
import time

# from vnpy.gateway.binance import BinanceGateway
from vnpy.gateway.binances import BinancesGateway
# from vnpy.gateway.bitmex import BitmexGateway
# from vnpy.gateway.futu import FutuGateway
# from vnpy.gateway.ib import IbGateway
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


def main():
    """"""
    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)
    engine_name = 'BINANCES'

    main_engine.add_gateway(BinancesGateway)
    setting = {
        "key": "bEZCKVAkJYugYErdlg5GAj7PGgh72ieFIVtDVYgUwJuE7M0vLFM7lN7JuQPYB0AL",
        "secret": "LGZXmPUe4iXqOWlmjiUHGvf7XsdLSBWe5HfXauJoxu8qR9RTeZMUqzTOhcRiAK9K",
        "会话数": 3,
        "服务器": ["REAL"],
        "合约模式": "正向",
        "代理地址": "",
        "代理端口": 0}
    main_engine.connect(setting, engine_name)
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    main_engine.write_log("主引擎创建成功")

    qapp.exec()

    pass

if __name__ == "__main__":
    main()