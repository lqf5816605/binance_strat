# flake8: noqa
import sys
sys.path.append('C:\\Workspace\\')
sys.path.append('C:\\Workspace\\vnpy\\')
from vnpy.event import EventEngine
import pandas as pd
import json
import os
import pickle
from vnpy.trader.constant import Direction, Exchange, Interval, OrderType, Offset
from vnpy.trader.object import HistoryRequest, SubscribeRequest, OrderRequest, CancelRequest
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
# from vnpy.gateway.ctptest import CtptestGateway
from vnpy.gateway.ctp import CtpGateway
import time
from sqlalchemy import create_engine
import sqlalchemy as sa
import psycopg2
from datetime import timedelta
from requests.auth import HTTPBasicAuth
import requests
import pymysql
pymysql.install_as_MySQLdb()


class FuturesInfo:
    time: str

    def __init__(self, symbol):
        self.symbol = symbol
        self.position_yesterday = 0
        self.position_today = 0
        self.cost_price = 0.0
        self.market_price = 0.0
        self.order_price = 0.0


class FuturesStrat(object):

    def __init__(self):

        self.main_engine = None
        self.engine_name = 'CTP'
        self.symbols = None
        self.symbol_timer = None
        self.mariadb_engine = None
        self.redshift_engine= None
        self.conn_mariadb = None
        self.conn_redshift = None
        self.timing_position = None
        self.current_date = None
        self.previous_date = None
        self.cur_balance = None
        self.futures_info = {}
        self.stock_cash_amount = 0
        self.atp_stock_portfolio_id = 121
        self.atp_futures_portfolio_id = 127
        self.atp_futures_algo_id = 123
        self.futures_osid = 4000005
        self.hedge_pct_yesterday = 1
        self.hedge_pct = 1

    def initiate(self):


        # self.conn = psycopg2.connect(dbname='timeseries', host='backtesting-dev.coqmt1duzsgx.us-east-1.redshift.amazonaws.com', port=5439, user='alex', password='Alx_123E')
        # self.conn = psycopg2.connect(dbname='atp', host='atp-dev.cjbwf6taixqt.us-east-1.rds.amazonaws.com', port=3306, user='atpuser', password='12_atpus3r_34!')
        self.mariadb_engine = create_engine('mysql+mysqldb://atpuser:12_atpus3r_34!@atp-dev.cjbwf6taixqt.us-east-1.rds.amazonaws.com:3306/atp')
        self.redshift_engine = create_engine('postgresql+psycopg2://jaguar_stage:H%w2flf^gjmY2uSa@backtesting-stage.coqmt1duzsgx.us-east-1.redshift.amazonaws.com:5439/timeseries')
        # postgresql+psycopg2://alex:Alx_123E@backtesting-dev.coqmt1duzsgx.us-east-1.redshift.amazonaws.com:5439/timeseries
        self.conn_mariadb = self.mariadb_engine.connect()
        self.conn_redshift = self.redshift_engine.connect()

        self.query_timing()
        self.current_date = pd.Timestamp.now().date()
        self.previous_date = self.timing_position.index[0].date()
        if self.current_date <= self.previous_date:
           print('current date and previous date wrong')

        self.query_atp_stock()

        event_engine = EventEngine()

        self.main_engine = MainEngine(event_engine)

        self.main_engine.add_gateway(CtpGateway)
        # main_window = MainWindow(main_engine, event_engine)
        # main_window.showMaximized()

        self.main_engine.write_log("主引擎创建成功")

        # simnow
        setting = {
            "用户名": "057802",
            "密码": "5816605",
            "经纪商代码": '9999',
            "交易服务器": "180.168.146.187:10100",
            "行情服务器": "180.168.146.187:10110",
            "产品名称": "simnow_client_test",
            "授权编码": 0000000000000000,
            "产品信息": ''
        }
        self.main_engine.connect(setting, self.engine_name)

        time.sleep(5)

        self.subscribe_quote()
        time.sleep(2)
        self.cur_balance = round(self.main_engine.get_all_accounts()[0].balance, 2)
        self.get_quote()
        self.get_futures_volume()
        self.get_trading()

    def query_timing(self):
        sql = 'select top 100 * from alex.if_timing order by TradingDay desc'
        self.timing_position = pd.read_sql_query(sql, self.conn_redshift)
        self.timing_position.index = pd.to_datetime(self.timing_position['tradedate'])
        sql_500 = 'select top 100 * from alex.ic_timing order by TradingDay desc'
        timing_position_500 = pd.read_sql_query(sql_500, self.conn_redshift)
        timing_position_500.index = pd.to_datetime(timing_position_500['tradedate'])
        self.symbol_timer = self.timing_position['symbol'].iloc[0]
        symbol_timer_500 = timing_position_500['symbol'].iloc[0]
        self.symbols = {self.symbol_timer:0, symbol_timer_500:0}
        self.futures_info[self.symbol_timer] = FuturesInfo(self.symbol_timer)
        print(2)

    def get_trading(self):
        this_info = self.futures_info[self.symbol_timer]
        # today long
        if this_info.position_today > 0:
            if this_info.position_yesterday == 0:
                open_volume = this_info.position_today - this_info.position_yesterday
                thisorder = OrderRequest(symbol=self.symbol_timer, exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.LONG, type=OrderType.LIMIT, price=this_info.market_price, volume=open_volume, offset=Offset.OPEN)

                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                this_info.cost_price = this_info.market_price
            elif this_info.position_yesterday >0:
                change_volume = this_info.position_today - this_info.position_yesterday
                if change_volume >= 1:
                    thisorder = OrderRequest(symbol=self.symbol_timer,
                                             exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                             direction=Direction.LONG, type=OrderType.LIMIT,
                                             price=this_info.market_price, volume=abs(change_volume), offset=Offset.OPEN)

                    thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                    this_info.cost_price = (this_info.cost_price * abs(
                        this_info.position_yesterday) + this_info.market_price * abs(
                        change_volume)) / (abs(this_info.position_yesterday) + abs(change_volume))

                elif change_volume <= -1:
                    thisorder = OrderRequest(symbol=self.symbol_timer,
                                             exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                             direction=Direction.SHORT, type=OrderType.LIMIT,
                                             price=this_info.market_price, volume=abs(change_volume), offset=Offset.CLOSE)

                    thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                    # this_info.cost_price = this_info.cost_price #cost_price does not change

            elif this_info.position_yesterday < 0:
                close_volume = this_info.position_yesterday
                open_volume = this_info.position_today
                thisorder = OrderRequest(symbol=self.symbol_timer, exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.LONG, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(close_volume), offset=Offset.CLOSE)
                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                time.sleep(1)
                thisorder = OrderRequest(symbol=self.symbol_timer,
                                         exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.LONG, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(open_volume), offset=Offset.OPEN)

                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                this_info.cost_price = this_info.market_price

        # today zero
        if this_info.position_today == 0:
            if this_info.position_yesterday == 0:
                pass
            elif this_info.position_yesterday >0:
                close_volume = this_info.position_yesterday

                thisorder = OrderRequest(symbol=self.symbol_timer,
                                         exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.SHORT, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(close_volume), offset=Offset.CLOSE)
                this_info.cost_price = 0
                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)

            elif this_info.position_yesterday < 0:
                close_volume = this_info.position_yesterday
                thisorder = OrderRequest(symbol=self.symbol_timer, exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.LONG, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(close_volume), offset=Offset.CLOSE)
                this_info.cost_price = 0
                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)

        # today short
        if this_info.position_today < 0:
            if this_info.position_yesterday == 0:
                open_volume = this_info.position_today - this_info.position_yesterday
                thisorder = OrderRequest(symbol=self.symbol_timer, exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.SHORT, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(open_volume), offset=Offset.OPEN)
                this_info.cost_price = this_info.market_price
                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)

            elif this_info.position_yesterday < 0:
                change_volume = this_info.position_today - this_info.position_yesterday
                if change_volume <= -1:
                    thisorder = OrderRequest(symbol=self.symbol_timer,
                                             exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                             direction=Direction.SHORT, type=OrderType.LIMIT,
                                             price=this_info.market_price, volume=abs(change_volume), offset=Offset.OPEN)

                    thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                    this_info.cost_price = (this_info.cost_price * abs(
                        this_info.position_yesterday) + this_info.market_price * abs(
                        change_volume)) / (abs(this_info.position_yesterday) + abs(change_volume))

                elif change_volume >= 1:
                    thisorder = OrderRequest(symbol=self.symbol_timer,
                                             exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                             direction=Direction.LONG, type=OrderType.LIMIT,
                                             price=this_info.market_price, volume=abs(change_volume), offset=Offset.CLOSE)

                    thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                    # this_info.cost_price = this_info.cost_price

            elif this_info.position_yesterday > 0:
                close_volume = this_info.position_yesterday
                open_volume = this_info.position_today
                thisorder = OrderRequest(symbol=self.symbol_timer, exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.SHORT, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(close_volume), offset=Offset.CLOSE)
                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                time.sleep(1)
                thisorder = OrderRequest(symbol=self.symbol_timer,
                                         exchange=self.main_engine.gateways[self.engine_name].exchanges[0],
                                         direction=Direction.SHORT, type=OrderType.LIMIT,
                                         price=this_info.market_price, volume=abs(open_volume), offset=Offset.OPEN)
                thisorderid = self.main_engine.send_order(thisorder, self.engine_name)
                this_info.cost_price = this_info.market_price

    def get_futures_volume(self):
        self.get_position()
        # today position
        this_info = self.futures_info[self.symbol_timer]
        if self.hedge_pct == 1:
            this_info.position_today = int(self.stock_cash_amount/1000000)
        elif self.hedge_pct == 0:
            this_info.position_today = 0
        elif self.hedge_pct == -1:
            this_info.position_today = -1 * int(self.stock_cash_amount/1000000)
        # yesterday position
        self.cur_balance = round(self.main_engine.get_all_accounts()[0].balance, 2)
        futures_positions = self.main_engine.engines['oms'].positions
        if len(futures_positions) ==0:
            this_info.position_yesterday = 0
        else:
            query_name = self.symbol_timer + '.' + self.main_engine.gateways[self.engine_name].exchanges[
                self.symbols[self.symbol_timer]].name
            query_position_long = query_name + '.' + '多'
            query_position_short = query_name + '.' + '空'
            if query_position_long in list(futures_positions.keys()):
                this_info.position_yesterday = futures_positions[query_position_long].volume
            elif query_position_short in list(futures_positions.keys()):
                this_info.position_yesterday = -1*futures_positions[query_position_short].volume
            else:
                this_info.position_yesterday = 0

    def get_position(self):
        # get today position
        if self.timing_position['position'].loc[self.previous_date] == 0:
            self.hedge_pct_yesterday = 0
            self.hedge_pct = self.hedge_pct_yesterday
            if self.timing_position['trade'].loc[self.previous_date] == -1:
                self.hedge_pct = -1.0  # 0.0
                # self.position_data['desired_wt'] = 0
            elif self.timing_position['trade'].loc[self.previous_date] == 1:
                self.hedge_pct = 1.0

        elif self.timing_position['position'].loc[self.previous_date] == 1:
            self.hedge_pct_yesterday = 1
            self.hedge_pct = self.hedge_pct_yesterday

            if self.timing_position['trade'].loc[self.previous_date] == -1:
                self.hedge_pct = -1.0  # 0.0
                # self.position_data['desired_wt'] = 0
            elif self.timing_position['trade'].loc[self.previous_date] == 100:
                self.hedge_pct = 0.0

        elif self.timing_position['position'].loc[self.previous_date] == -1:
            self.hedge_pct_yesterday = -1
            self.hedge_pct = self.hedge_pct_yesterday

            if self.timing_position['trade'].loc[self.previous_date] == 1:
                self.hedge_pct = 1.0  # 0.0
                # self.position_data['desired_wt'] = 0
            elif self.timing_position['trade'].loc[self.previous_date] == 100 or self.timing_position[
                'trade'].loc[self.previous_date] == 200:

                self.hedge_pct = 0.0
        # get yesterday position

    def query_atp_stock(self):
        sql_idx = "select * from atp.DailyValue \
                    where PortfolioID ={} \
                    order by date desc".format(self.atp_stock_portfolio_id)
        df_dailyvalue = pd.read_sql_query(sql_idx, self.conn_mariadb)
        self.stock_cash_amount = df_dailyvalue[df_dailyvalue['date'] == self.previous_date]['EquityWithLoanValue'].iloc[0]
        #
        sql_position = "select * from atp.DailyPosition \
                            where PortfolioID ={} \
                            order by Date desc".format(self.atp_futures_portfolio_id)
        df_dailyposition = pd.read_sql_query(sql_position, self.conn_mariadb)

        this_position = df_dailyposition[(df_dailyposition['Date'] == self.previous_date) &(
            df_dailyposition['Osid'] == self.futures_osid)]

        if len(this_position) != 0:
            this_info = self.futures_info[self.symbol_timer]
            this_info.cost_price = this_position['AvgPrice'].iloc[0]

        # if today is uploaded, then use today average cost price as latest
        this_position_refresh = df_dailyposition[(df_dailyposition['Date'] == self.current_date) & (
                df_dailyposition['Osid'] == self.futures_osid)]

        if len(this_position_refresh) != 0:
            this_info = self.futures_info[self.symbol_timer]
            this_info.cost_price = this_position_refresh['AvgPrice'].iloc[0]

    def update_future_balance(self):
        query = "UPDATE atp.DailyValue SET EquityWithLoanValue = {} \
                  WHERE PortfolioID = {} and date = '{}';".format(self.cur_balance, self.atp_futures_portfolio_id,self.current_date.strftime('%Y-%m-%d'))

        self.conn_mariadb.execute(sa.text(query))
        print(2)

    def query_atp_futures(self):
        pass

    def subscribe_quote(self):

        for symbol, i in self.symbols.items():
            quote = SubscribeRequest(symbol, self.main_engine.gateways[self.engine_name].exchanges[i])
            self.main_engine.subscribe(quote, self.engine_name)

    def get_quote(self):
        x = self.main_engine.engines['oms'].ticks
        info = self.symbol_timer + "." + self.main_engine.gateways[self.engine_name].exchanges[self.symbols[self.symbol_timer]].name
        if info not in list(x.keys()):

            print('no data, resubscribe')
            quote = SubscribeRequest(self.symbol_timer, self.main_engine.gateways[self.engine_name].exchanges[self.symbols[self.symbol_timer]])
            self.main_engine.subscribe(quote, self.engine_name)
            self.main_engine.engines['oms'].register_event()
        else:
            x = x[info]
            this_info = self.futures_info[self.symbol_timer]
            this_info.market_price = x.last_price

    def main_logic(self):

        while True:

            time.sleep(60)
            self.get_quote()
            self.get_balance()
            # self.update_future_balance()
            self.submit_portfolio()

    def get_balance(self):
        self.cur_balance = round(self.main_engine.get_all_accounts()[0].balance, 2)

    def load_positions(self):
        positions = list()
        for pos in [1]:
            position = dict()
            position["date"] = self.current_date.strftime('%Y-%m-%d')
            position["localSymbol"] = 'IFLX0'
            this_info = self.futures_info[self.symbol_timer]
            if this_info.position_today > 0:
                pos_type = '多'
            elif this_info.position_today < 0:
                pos_type = '空'

            query_name = self.symbol_timer + '.' + self.main_engine.gateways[self.engine_name].exchanges[
                self.symbols[self.symbol_timer]].name
            query_position_name = query_name + '.' + pos_type
            try:
                volume = self.main_engine.engines['oms'].positions[query_position_name].volume
            except:
                volume = 0

            this_info = self.futures_info[self.symbol_timer]
            position["quantity"] = str(volume)
            position["avgPrice"] = str(this_info.cost_price)
            position["marketPrice"] = str(this_info.market_price)
            position["exchangeRate"] = str(1.0)
            position["brokerCurrency"] = 'CNY'
            position["exchange"] = 'CFFEX'
            # this is required for India as won_symbol is different than local symbol
            position["wonOsid"] = self.futures_osid
            positions.append(position)
        return positions

    def submit_portfolio(self):
        data = dict()
        data["date"] = self.current_date.strftime('%Y-%m-%d')
        cash = self.cur_balance
        data["cashAmount"] = str(cash)
        data["equityWithLoanValue"] = str(cash)
        data["availableFunds"] = str(cash)
        data['currency'] = 'CNY'
        data['positions'] = self.load_positions()

        print("Post portfolio for date {}".format(data.get('date')))
        url = "{0}://{1}/atp/api/algo/{2}/portfolio/summary.json".format('http', 'atpdev', self.atp_futures_algo_id)
        print('POST ' + url)
        # log.info(data)
        try:
            r = requests.post(url, json=data, auth=HTTPBasicAuth('AlgoQAAccount1', 'Dai2016!'))
        except requests.exceptions.RequestException as e:
            msg = "Error posting portfolio to ATP: " + str(e)
            print(msg)
        else:
            self.check_response(r)
        print('atp update success')


    def check_response(self, req):
        if req.status_code == 200:
            atp_resp = req.json()
            resp_header = atp_resp['responseHeader']
            if resp_header['error']:
                error_msg = resp_header['errorDesc']
                print(error_msg)
        else:
            error_msg = "Error from ATP: Status code = {0}".format(req.status_code)
            print(error_msg)

def main():
    future_strat = FuturesStrat()
    future_strat.initiate()
    future_strat.main_logic()


if __name__ == "__main__":
    main()