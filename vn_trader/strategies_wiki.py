#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import talib 
from datetime import datetime, timedelta

import matplotlib as mpl


def strat_ma_cross(data, curdata, params):

    short_tm_buy = params['buy']['short_tm']
    long_tm_buy = params['buy']['long_tm']
    interval_buy = params['buy']['interval']
    short_tm_sell = params['sell']['short_tm']
    long_tm_sell = params['sell']['long_tm']
    interval_sell = params['sell']['interval']
    data['short_ma_buy'] = data['close'].rolling(short_tm_buy).mean()
    data['long_ma_buy'] = data['close'].rolling(long_tm_buy).mean()
    data['short_ma_sell'] = data['close'].rolling(short_tm_sell).mean()
    data['long_ma_sell'] = data['close'].rolling(long_tm_sell).mean()
    data['change'] = data['close']/data['close'].shift(1)-1.0
    data['ma_change_buy'] = data['short_ma_buy'] - data['long_ma_buy']
    data['ma_change_sell'] = data['short_ma_sell'] - data['long_ma_sell']
    data['signal'] = 0.0
    if interval_buy != 0:
        data['signal'].mask((data['ma_change_buy'] > 0) & (data['ma_change_buy'].shift(1) < 0) & (abs(data['change'])>0.01), 1.0, inplace=True)
    if interval_sell != 0:
        data['signal'].mask((data['ma_change_sell'] < 0) & (data['ma_change_sell'].shift(1) > 0) & (abs(data['change'])>0.01), -1.0, inplace=True)
    msg = '{} , short ma buy {}, long ma buy {}'.format(curdata.symbol, data['short_ma_buy'].iloc[-1], data['long_ma_buy'].iloc[-1])
    return data['signal'].iloc[-1], msg


def strat_breakout_volume(data, curdata,params):
    interval_buy = params['buy']['interval_box']
    thld_buy = params['buy']['thld']
    chg_thld_buy = params['buy']['chg_thld']
    interval_sell = params['sell']['interval_box']
    thld_sell = params['sell']['thld']
    chg_thld_sell = params['sell']['chg_thld']
    data['chg'] = data['close'] / data['close'].shift(1) - 1.0
    data['volume_mean_buy'] = data['volume'].rolling(interval_buy).mean()
    data['volume_std_buy'] = data['volume'].rolling(interval_buy).std()
    data['volume_up_buy'] = data['volume_mean_buy'] + thld_buy * data['volume_std_buy']
    data['volume_down_buy'] = data['volume_mean_buy'] - thld_buy * data['volume_std_buy']
    if interval_buy!=0:
        data['high_interval_buy'] = data['high'].rolling(interval_buy).max().shift(1)
        data['low_interval_buy'] = data['low'].rolling(interval_buy).min().shift(1)
        data['interval_change_buy'] = data['high_interval_buy'] / data['low_interval_buy'] - 1.0
    else:
        data['interval_change_buy'] = 1
    #

    data['volume_mean_sell'] = data['volume'].rolling(interval_sell).mean()
    data['volume_std_sell'] = data['volume'].rolling(interval_sell).std()
    data['volume_up_sell'] = data['volume_mean_sell'] + thld_sell * data['volume_std_sell']
    data['volume_down_sell'] = data['volume_mean_sell'] - thld_sell * data['volume_std_sell']
    if interval_sell!=0:
        data['high_interval_sell'] = data['high'].rolling(interval_sell).max().shift(1)
        data['low_interval_sell'] = data['low'].rolling(interval_sell).min().shift(1)
        data['interval_change_sell'] = data['high_interval_sell'] / data['low_interval_sell'] - 1.0
    else:
        data['interval_change_sell'] = 1
    data['signal'] = 0.0
    data['signal'].mask(
                (data['volume'] > data['volume_up_buy']) & (data['chg'] > 0) & (data['interval_change_buy'].shift(1) < chg_thld_buy) , 1.0,
                inplace=True)
    data['signal'].mask(
                (data['volume'] > data['volume_up_sell']) & (data['chg'] < 0) & (data['interval_change_sell'].shift(1) < chg_thld_sell) , -1.0,
                inplace=True)

    msg = '{} , volume {}, large threshold {}, interval change {}'.format(curdata.symbol, data['volume'].iloc[-1], data['volume_up_buy'].iloc[-1],
                                                        data['interval_change_buy'].iloc[-1])
    return data['signal'].iloc[-1], msg


def strat_needle(data, curdata,params):
    interval_buy = params['buy']['interval_chg']
    thld_buy = params['buy']['thld']
    interval_sell = params['sell']['interval_chg']
    thld_sell = params['sell']['thld']
    data['chg'] = data['close'] / data['close'].shift(1) - 1.0
    data['volume_mean_buy'] = data['volume'].rolling(interval_buy).mean()
    data['volume_std_buy'] = data['volume'].rolling(interval_buy).std()
    data['volume_up_buy'] = data['volume_mean_buy'] + thld_buy * data['volume_std_buy']
    data['volume_down_buy'] = data['volume_mean_buy'] - thld_buy * data['volume_std_buy']
    #
    data['volume_mean_sell'] = data['volume'].rolling(interval_sell).mean()
    data['volume_std_sell'] = data['volume'].rolling(interval_sell).std()
    data['volume_up_sell'] = data['volume_mean_sell'] + thld_sell * data['volume_std_sell']
    data['volume_down_sell'] = data['volume_mean_sell'] - thld_sell * data['volume_std_sell']
    #
    data['chg_sum_buy'] = data['close'] / data['close'].shift(interval_buy) - 1.0
    data['chg_sum_sell'] = data['close'] / data['close'].shift(interval_sell) - 1.0
    data['bar'] = (data['close'] - data['open']) / (data['high'] - data['low'] + 0.000000001)

    data['signal'] = 0.0
    if interval_buy != 0:
        data['signal'].mask(
            (data['volume'].shift(1) > data['volume_up_buy'].shift(1)) & (abs(data['bar'].shift(1)) < 0.2) & (
                        data['chg'] > 0) & (data['chg_sum_buy'].shift(1) < 0), 1.0,
            inplace=True)
    if interval_sell != 0:
        data['signal'].mask(
            (data['volume'].shift(1) > data['volume_up_sell'].shift(1)) & (abs(data['bar'].shift(1)) < 0.2) & (
                        data['chg'] < 0) & (data['chg_sum_sell'].shift(1) > 0.0), -1.0,
            inplace=True)

    msg = '{} , volume buy {}, bar {}'.format(curdata.symbol, data['volume_up_buy'].iloc[-1],
                                                        data['bar'].iloc[-1])
    return data['signal'].iloc[-1], msg


def strat_many_bars(data, curdata, params):
    interval_bars_sell = params['sell']['interval_bars']
    data['change'] = data['close']/data['close'].shift(1) - 1.0
    data['short_ma'] = data['close'].rolling(8).mean()
    data['long_ma'] = data['close'].rolling(24).mean()
    data['sign_positive'] = data['change'] > 0
    data['sign_negative'] = data['change'] < 0
    data['magnitude'] = abs(data['change']) > 0.01
    data['count_magnitude'] = data['magnitude'].rolling(3).sum()
    data['count_positive'] = data['sign_positive'].rolling(interval_bars_sell).sum()
    data['count_negative'] = data['sign_negative'].rolling(interval_bars_sell).sum()
    data['signal'] = 0.0
    if interval_bars_sell!=0:
        data['signal'].mask((data['count_negative'] == (interval_bars_sell - 1)) & (data['short_ma'] > data['long_ma']),
                       -1.0, inplace=True)

    msg = '{} , count bars {}'.format(curdata.symbol, data['count_negative'].iloc[-1])
    return data['signal'].iloc[-1], msg


def strat_breakout_three_doji(data, curdata,params):
    interval_buy = params['buy']['interval_box']
    thld_buy = params['buy']['thld']
    interval_sell = params['sell']['interval_box']
    thld_sell = params['sell']['thld']
    data['chg'] = data['close'] / data['close'].shift(1) - 1.0
    data['volume_mean_buy'] = data['volume'].rolling(interval_buy).mean()
    data['volume_std_buy'] = data['volume'].rolling(interval_buy).std()
    data['volume_up_buy'] = data['volume_mean_buy'] + thld_buy * data['volume_std_buy']
    data['volume_down_buy'] = data['volume_mean_buy'] - thld_buy * data['volume_std_buy']
    #
    data['volume_mean_sell'] = data['volume'].rolling(interval_sell).mean()
    data['volume_std_sell'] = data['volume'].rolling(interval_sell).std()
    data['volume_up_sell'] = data['volume_mean_sell'] + thld_sell * data['volume_std_sell']
    data['volume_down_sell'] = data['volume_mean_sell'] - thld_sell * data['volume_std_sell']
    #

    data['bar'] = (data['close'] - data['open']) / (data['high'] - data['low'] + 0.000000001)

    data['signal'] = 0.0
    if interval_buy != 0:
        data['signal'].mask(
            (data['volume'] > data['volume_up_buy']) & (abs(data['bar'].shift(1)) < 0.5) & (abs(data['bar'].shift(2)) < 0.5) & (data['chg'] >0.005), 1.0,
            inplace=True)
    if interval_sell != 0:
        data['signal'].mask(
            (data['volume'] > data['volume_up_sell']) & (abs(data['bar'].shift(1)) < 0.5) & (abs(data['bar'].shift(2)) < 0.5) & (data['chg'] < -0.005), 0.5,
            inplace=True)

    msg = '{} , volume buy {}, bar {}'.format(curdata.symbol, data['volume_up_buy'].iloc[-1],
                                                        data['bar'].iloc[-1])
    return data['signal'].iloc[-1], msg


def strat_pullback(data, curdata, params):

    short_tm_buy = params['buy']['short_tm']
    long_tm_buy = params['buy']['long_tm']
    interval_buy = params['buy']['interval']
    # short_tm_sell = params['sell']['short_tm']
    # long_tm_sell = params['sell']['long_tm']
    # interval_sell = params['sell']['interval']
    data['short_ma_buy'] = data['close'].rolling(short_tm_buy).mean()
    data['long_ma_buy'] = data['close'].rolling(long_tm_buy).mean()
    # data['short_ma_sell'] = data['close'].rolling(short_tm_sell).mean()
    # data['long_ma_sell'] = data['close'].rolling(long_tm_sell).mean()
    data['change'] = data['close']/data['close'].shift(1)-1.0
    data['ma_change_buy'] = data['short_ma_buy'] - data['long_ma_buy']
    # data['ma_change_sell'] = data['short_ma_sell'] - data['long_ma_sell']
    data['signal'] = 0.0

    if interval_buy != 0:
        data['signal'].mask((data['ma_change_buy'] > 0) & (data['close']> data['short_ma_buy']) & (data['change']< -0.01), 1.0, inplace=True)
    # if interval_sell != 0:
    #     data['signal'].mask((data['ma_change_sell'] < 0) & (data['close']< data['short_ma_sell']) & (data['change']> 0.01), -1.0, inplace=True)
    msg = '{} , short ma buy {}, long ma buy {}'.format(curdata.symbol, data['short_ma_buy'].iloc[-1], data['long_ma_buy'].iloc[-1])
    return data['signal'].iloc[-1], msg