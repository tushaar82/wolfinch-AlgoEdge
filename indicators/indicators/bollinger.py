# '''
#  Desc: Bollinger Bands (Overlap Studies) implementation using tulip
#  https://tulipindicators.org/bband
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

class BBANDS (Indicator):
    '''
    Bollinger Bands (Overlap Studies) market indicator implementation using TA library
    '''
    
    def __init__(self, name, period=20, stddev=2):
        self.name = name
        self.period = period
        self.stddev = stddev
                
    def calculate(self, candles):        
        candles_len = len(candles)
        if candles_len < self.period:
            return float(0)
        
        val_array = np.array([float(x['ohlc'].close) for x in candles[-self.period:]])
        
        #calculate 
        (upperband, middleband, lowerband) = ti.bbands (val_array, period=self.period, stddev=self.stddev)
        
        return (upperband[-1], middleband[-1], lowerband[-1])
        
