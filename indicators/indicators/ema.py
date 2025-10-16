# '''
#  Desc: Market Exponential Moving Average (EMA) implementation using tulip
#  https://tulipindicators.org/ema
#
#  Copyright: (c) 2017-2020 Joshith Rayaroth Koderi
#  This file is part of Wolfinch.
# 
#  Wolfinch is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  Wolfinch is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with Wolfinch.  If not, see <https://www.gnu.org/licenses/>.
# '''

# from decimal import Decimal
from .indicator import Indicator
import numpy as np
import tulipy as ti

class EMA (Indicator):
    '''
    Exponential moving Average (EMA) market indicator implementation using TA library
    '''
    
    def __init__(self, name, period=12):
        self.name = name
        self.period = period
                
    def calculate(self, candles):        
        candles_len = len(candles)
        if candles_len < self.period:
            return float(0)
        
        val_array = np.array([float(x['ohlc'].close) for x in candles[-self.period:]])
        
        #calculate ema
        cur_ema = ti.ema (val_array, self.period)
        
#         log.info ("TA_EMA: %g"%cur_ema)
        return float(cur_ema[-1])
        
