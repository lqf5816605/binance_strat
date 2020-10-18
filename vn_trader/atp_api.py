import json
import requests
import pytz
from requests.auth import HTTPBasicAuth
import ote.utils
from ote.broker.integration.bridge import BridgeOrder
# from ote.broker.integration.ib_broker_india_api import IndiaInteractiveBrokerApi
from ote.broker.integration.exec_strategy_name import *

logger = ote.utils.setup_logging('atp-api')


class AtpError(Exception):
    pass


class AtpApi():
    def __init__(self, tzname, protocol, host, algo_id, user, pwd, broker_api_service=None):
        self.tzname = tzname
        self.protocol = protocol
        self.host = host
        self.algo_id = algo_id
        self.user = user
        self.password = pwd
        self.broker_api_service = broker_api_service

    def check_response(self, req):
        if req.status_code == 200:
            atp_resp = req.json()
            resp_header = atp_resp['responseHeader']
            if resp_header['error']:
                error_msg = resp_header['errorDesc']
                error_msg = "Error from ATP: " + (error_msg if error_msg is not None else "No detail")
                logger.error(error_msg)
                raise AtpError(error_msg)
        else:
            error_msg = "Error from ATP: Status code = {0}".format(req.status_code)
            logger.error(error_msg)
            raise AtpError(error_msg)

    def load_positions(self, bridge_positions, trade_date):
        positions = list()
        for pos in bridge_positions:
            if pos.quantity != 0:
                position = dict()
                position["date"] = trade_date.strftime('%Y-%m-%d')
                position["localSymbol"] = pos.instrument.local_symbol
                position["quantity"] = str(pos.quantity)
                position["avgPrice"] = str(pos.average_cost)
                position["marketPrice"] = str(pos.market_price)
                position["exchangeRate"] = str(pos.exchange_rate)
                position["brokerCurrency"] = pos.currency
                position["exchange"] = pos.instrument.exchange if pos.instrument.exchange else 'NA'
                # this is required for India as won_symbol is different than local symbol
                position["wonOsid"] = pos.instrument.osid
                positions.append(position)
        return positions

    def submit_portfolio(self, bridge_portfolio):
        data = dict()
        trade_date = bridge_portfolio.as_of_date
        data["date"] = trade_date.strftime('%Y-%m-%d')
        data["cashAmount"] = str(bridge_portfolio.cash)
        data["equityWithLoanValue"] = str(bridge_portfolio.net)
        data["availableFunds"] = str(bridge_portfolio.available_fund)
        data['currency'] = bridge_portfolio.currency
        data['positions'] = self.load_positions(bridge_portfolio.positions.values(), trade_date)

        logger.info("Post portfolio for date {}".format(data.get('date')))
        url = "{0}://{1}/atp/api/algo/{2}/portfolio/summary.json".format(self.protocol, self.host, self.algo_id)
        logger.info('POST ' + url)
        # log.info(data)
        try:
            r = requests.post(url, json=data, auth=HTTPBasicAuth(self.user, self.password))
        except requests.exceptions.RequestException as e:
            msg = "Error posting portfolio to ATP: " + str(e)
            logger.error(msg)
            raise AtpError(msg)
        else:
            self.check_response(r)

    def load_executions(self, bridge_executions, use_exec_id=False):
        executions = list()
        for execution in bridge_executions:
            ex = dict()
            ex["filledPrice"] = str(execution.filled_price)
            ex["filledShares"] = str(abs(execution.filled_quantity))
            ex["commission"] = str(execution.commission)
            if use_exec_id:
                ex['brokerExecID'] = str(execution.broker_exec_id)
            ex["execTime"] = execution.filled_time.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S")
            logger.info(ex)
            executions.append(ex)
        return executions

    def get_algo_attribute_str(self, kw):
        prefix = EXEC_STRATEGY_LABEL + "_"
        attribute = {k[len(prefix):]: v for k, v in kw.items() if k.startswith(prefix)}
        return json.dumps(attribute)

    def submit_order(self, bridge_order: BridgeOrder, use_exec_id=False):
        order = dict()
        order["orderDate"] = str(bridge_order.date.astimezone(pytz.timezone(self.tzname)).date())
        order["localSymbol"] = bridge_order.instrument.local_symbol
        order["symbol"] = bridge_order.instrument.won_symbol
        order["action"] = 'Buy' if bridge_order.quantity > 0 else 'Sell'
        order["numberShares"] = str(abs(bridge_order.quantity))
        order["priceType"] = 'Market'
        order["tradePrice"] = '0'
        order["tag"] = str(bridge_order.broker_order_id)
        if bridge_order.limit_price is not None:
            order["priceType"] = 'Limit'
            order["tradePrice"] = str(bridge_order.limit_price)
        if bridge_order.stop_price is not None:
            order['stopPrice'] = str(bridge_order.stop_price)
        order["submitTime"] = bridge_order.date.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S")
        order['osid'] = str(bridge_order.instrument.osid)

        if bridge_order.kwargs.get(EXEC_STRATEGY_LABEL, '') in [EXEC_STRATEGY_PERCENT_OF_VOLUME]:
            order['algoExecType'] = bridge_order.kwargs[EXEC_STRATEGY_LABEL]
            order['algoAttribute'] = self.get_algo_attribute_str(bridge_order.kwargs)

        so = dict()
        so["localSymbol"] = order["localSymbol"]
        so["symbol"] = order["symbol"]
        so["numberShares"] = order["numberShares"]
        so["tradePrice"] = order["tradePrice"]
        so["brokerOrderID"] = str(bridge_order.broker_order_id)
        so["executions"] = self.load_executions(bridge_order.executions.values(), use_exec_id=use_exec_id)
        order["suborders"] = [so]

        msg = "Posting order: {0} {1} shares of {2}, osid={3}" \
            .format(order['action'], order['numberShares'], order['localSymbol'], order['osid'])
        logger.info(msg)
        if isinstance(self.broker_api_service, ote.broker.integration.ib_broker_india_api.IndiaInteractiveBrokerApi):
            url = "{0}://{1}/atp/api/algo/{2}/addupdatezerodhaorder.json".format(self.protocol, self.host, self.algo_id)
        else:
            url = "{0}://{1}/atp/api/algo/{2}/addziplineorder.json".format(self.protocol, self.host, self.algo_id)

        logger.info(url)
        logger.debug(order)
        try:
            r = requests.post(url, json=order, auth=HTTPBasicAuth(self.user, self.password))
        except requests.exceptions.RequestException as e:
            msg = "Error posting order to ATP: " + str(e)
            logger.error(msg)
            raise AtpError(msg)
        else:
            self.check_response(r)

    def pull_portfolio(self, date):
        data = {}
        url = "{0}://{1}/atp/api/algo/{2}/portfolio/summaryview.json?date={3}" \
            .format(self.protocol, self.host, self.algo_id, date.strftime("%Y%m%d"))
        logger.info('GET ' + url)
        r = requests.get(url, auth=HTTPBasicAuth(self.user, self.password))
        if r.status_code == 200:
            atp_resp = r.json()
            resp_header = atp_resp['responseHeader']
            if resp_header['error']:
                desp = resp_header['errorDesc']
                msg = "Error pulling portfolio from ATP: " + (str(desp) if desp is not None else 'No value.')
                logger.error(msg)
                raise AtpError(msg)
            else:
                data = atp_resp.get('data')
        else:
            msg = "Error pulling portfolio from ATP: Status code = {0}".format(r.status_code)
            logger.error(msg)
            raise AtpError(msg)
        return data

    def pull_orders(self, date):
        data = []
        url = "{0}://{1}/atp/api/algo/{2}/order.json?startdate={3}&enddate={3}" \
            .format(self.protocol, self.host, self.algo_id, date.strftime("%Y%m%d"))
        logger.info(url)
        r = requests.get(url, auth=HTTPBasicAuth(self.user, self.password))
        if r.status_code == 200:
            atp_resp = r.json()
            resp_header = atp_resp['responseHeader']
            if resp_header['error']:
                msg = resp_header['errorDesc']
                logger.error(msg)
                raise AtpError(msg)
            else:
                data = atp_resp.get('data')
        else:
            logger.error("Error pulling orders from ATP")
            raise AtpError("Error pulling orders from ATP")
        return data

    def send_notification(self, subject, body, prefix_algo=False, is_html=False):
        url = "{0}://{1}/atp/api/algo/{2}/notification.json?html={3}&prefixAlgoName={4}" \
            .format(self.protocol, self.host, self.algo_id,
                    "true" if is_html else "false", "true" if prefix_algo else "false")
        logger.info('POST ' + url)
        content = {'subject': subject}
        if is_html:
            content['htmlBody'] = body
        else:
            content['textBody'] = body
        try:
            r = requests.post(url, json=content, auth=HTTPBasicAuth(self.user, self.password))
        except requests.exceptions.RequestException as e:
            msg = "Error sending email from ATP: " + str(e)
            logger.error(msg)
            raise AtpError(msg)
        else:
            self.check_response(r)

    def run_eod(self, date):
        date_str = date.strftime("%Y%m%d")
        msg = "Running algo EOD process on {}".format(date_str)
        logger.info(msg)
        url = "{0}://{1}/atp/api/algo/{2}/portfolio/runeod.json".format(self.protocol, self.host, self.algo_id)
        logger.info('POST ' + url)
        try:
            r = requests.post(url, auth=HTTPBasicAuth(self.user, self.password))
        except requests.exceptions.RequestException as e:
            msg = "Error posting EOD to ATP: " + str(e)
            logger.error(msg)
            raise AtpError(msg)
        else:
            self.check_response(r)
