import pandas as pd
import numpy as np

SYMBOLS = ['YFIIUSDT', 'SUSHIUSDT', 'UNIUSDT', 'TRBUSDT']


def param_load():
    params = {}
    params['YFIIUSDT'] = {
        'ma_cross':
            {'buy':
        {
        'short_tm': 0, 'long_tm':0, 'interval':0
        },
            'sell':

        {'short_tm': 0, 'long_tm':0, 'interval':0}
    },
        'breakout_volume':{'buy':
        {
        'interval_box': 24, 'thld':4, 'chg_thld':0.15, 'interval':8
        },'sell':

        {'interval_box': 24, 'thld':4, 'chg_thld':0.15, 'interval':8}
    },
        'needle':{'buy':
        {
        'interval_chg': 8, 'thld':2, 'interval':8
        },'sell':

        {'interval_chg': 16, 'thld':1, 'interval':8}
    },
        'many_bars':{'sell':
        {
        'interval_bars': 7, 'interval':8
        }
    },
        'breakout_three_doji':{'buy':
        {
        'interval_box': 16, 'thld':2, 'interval':4
        },'sell':

        {'interval_box': 0, 'thld':0, 'interval':0}
    }, 'pullback':{'buy':
        {
        'short_tm':8, 'long_tm':16, 'interval':4
        }
    }}

    params['SUSHIUSDT'] = {
        'ma_cross':{
            'buy':{
        'short_tm': 0, 'long_tm':0, 'interval':0
        },
        'sell':{
        'short_tm': 0, 'long_tm':0, 'interval':0
        }
    },
        'breakout_volume':{'buy':
        {
        'interval_box': 24, 'thld':4, 'chg_thld':0.1, 'interval':16
        },'sell':

        {'interval_box': 8, 'thld':2, 'chg_thld':0.1, 'interval':2}
    },
        'needle':{'buy':
        {
        'interval_chg': 8, 'thld':2, 'interval':4
        },'sell':

        {'interval_chg': 16, 'thld':1, 'interval':4}
    },
        'many_bars':{'sell':
        {
        'interval_bars': 7, 'interval':8
        }
    },
        'breakout_three_doji':{'buy':
        {
        'interval_box': 24, 'thld':2, 'interval':2
        },'sell':

        {'interval_box': 8, 'thld':2, 'interval':2}
    },'pullback':{'buy':
        {
        'short_tm':4, 'long_tm':24, 'interval':4
        }
    }}

    params['UNIUSDT'] = {
        'ma_cross': {
            'buy': {
                'short_tm': 2, 'long_tm': 64, 'interval': 4
            },
            'sell': {
                'short_tm': 8, 'long_tm': 64, 'interval': 6
            }
        },
        'breakout_volume':{'buy':
        {
        'interval_box': 16, 'thld':2, 'chg_thld':0.15, 'interval':2
        },'sell':

        {'interval_box': 16, 'thld':2, 'chg_thld':0.1, 'interval':2}
    },
        'needle':{'buy':
        {
        'interval_chg': 4, 'thld':1, 'interval':4
        },'sell':

        {'interval_chg': 16, 'thld':1, 'interval':16}
    },
        'many_bars':{'sell':
        {
        'interval_bars': 7, 'interval':8
        }
    },
        'breakout_three_doji':{'buy':
        {
        'interval_box': 16, 'thld':1, 'interval':2
        },'sell':

        {'interval_box': 0, 'thld':0, 'interval':0}
    },'pullback':{'buy':
        {
        'short_tm':0, 'long_tm':0, 'interval':0
        }
    }}

    params['TRBUSDT'] = {
        'ma_cross': {
            'buy': {
                'short_tm': 8, 'long_tm': 64, 'interval': 4
            },
            'sell': {
                'short_tm': 2, 'long_tm': 24, 'interval': 4
            }
        },
        'breakout_volume':{'buy':
        {
        'interval_box': 0, 'thld':0, 'chg_thld':0, 'interval':0
        },'sell':

        {'interval_box': 24, 'thld':2, 'chg_thld':0.1, 'interval':2}
    },
        'needle':{'buy':
        {
        'interval_chg': 0, 'thld':0, 'interval':0
        },'sell':

        {'interval_chg': 8, 'thld':2, 'interval':4}
    },
        'many_bars':{'sell':
        {
        'interval_bars': 7, 'interval':8
        }
    },
        'breakout_three_doji':{'buy':
        {
        'interval_box': 0, 'thld':0, 'interval':0
        },'sell':

        {'interval_box': 24, 'thld':2, 'interval':4}
    },'pullback':{'buy':
        {
        'short_tm':4, 'long_tm':16, 'interval':4
        }
    }}

    params['WAVESUSDT'] = {
        'ma_cross':
            {'buy':
                {
                    'short_tm': 2, 'long_tm': 16, 'interval': 6
                },
                'sell':

                    {'short_tm': 0, 'long_tm': 0, 'interval': 0}
            },
        'breakout_volume': {'buy':
            {
                'interval_box': 24, 'thld': 4, 'chg_thld': 0.15, 'interval': 2
            }, 'sell':

            {'interval_box': 0, 'thld': 0, 'chg_thld': 0, 'interval': 0}
        },
        'needle': {'buy':
            {
                'interval_chg': 0, 'thld': 0, 'interval': 0
            }, 'sell':

            {'interval_chg': 0, 'thld': 0, 'interval': 0}
        },
        'many_bars': {'sell':
            {
                'interval_bars': 7, 'interval': 8
            }
        },
        'breakout_three_doji': {'buy':
            {
                'interval_box': 8, 'thld': 2, 'interval': 2
            }, 'sell':

            {'interval_box': 0, 'thld': 0, 'interval': 0}
        },'pullback':{'buy':
        {
        'short_tm':0, 'long_tm':0, 'interval':0
        }
    }}

    return params