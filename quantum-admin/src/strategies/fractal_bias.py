"""
Fractal Bias Strategy for Freqtrade

A multi-timeframe strategy based on fractal market theory:
- Uses Williams Fractals for trend identification
- Combines multiple timeframes for bias determination
- Implements proper risk management with dynamic position sizing
"""
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, CategoricalParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List, Optional
import numpy as np


class FractalBias(IStrategy):
    """
    Fractal Bias Strategy
    
    Based on Bill Williams' Fractal Theory combined with multi-timeframe analysis.
    
    Key Concepts:
    - Fractals identify local support/resistance levels
    - Higher timeframe bias determines trade direction
    - Lower timeframe fractals provide entry signals
    - Alligator indicator for trend confirmation
    """
    
    # Strategy interface version
    INTERFACE_VERSION = 3
    
    # Can this strategy go short?
    can_short: bool = True
    
    # Minimal ROI designed for the strategy
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }
    
    # Optimal stoploss
    stoploss = -0.08
    
    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True
    
    # Timeframe
    timeframe = '5m'
    
    # Process only new candles
    process_only_new_candles = True
    
    # These values can be overridden in config
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    
    # Startup candle count
    startup_candle_count: int = 200
    
    # Hyperopt parameters
    # Fractal period for Williams Fractals
    fractal_period = IntParameter(2, 10, default=5, space='buy', optimize=True)
    
    # EMA periods for trend
    ema_short = IntParameter(8, 21, default=13, space='buy', optimize=True)
    ema_long = IntParameter(21, 55, default=34, space='buy', optimize=True)
    
    # RSI parameters
    rsi_period = IntParameter(7, 21, default=14, space='buy', optimize=True)
    rsi_overbought = IntParameter(65, 85, default=70, space='sell', optimize=True)
    rsi_oversold = IntParameter(15, 35, default=30, space='buy', optimize=True)
    
    # ADX for trend strength
    adx_period = IntParameter(7, 21, default=14, space='buy', optimize=True)
    adx_threshold = IntParameter(20, 30, default=25, space='buy', optimize=True)
    
    # ATR for volatility-based stops
    atr_period = IntParameter(7, 21, default=14, space='buy', optimize=True)
    atr_multiplier = DecimalParameter(1.5, 3.0, default=2.0, space='buy', optimize=True)
    
    # Higher timeframe for bias
    informative_timeframe = '1h'
    
    def informative_pairs(self) -> List[tuple]:
        """Define additional informative pairs for multi-timeframe analysis"""
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.informative_timeframe) for pair in pairs]
        return informative_pairs
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Populate indicators for the strategy"""
        
        # Get informative timeframe data
        informative = self.dp.get_pair_dataframe(
            pair=metadata['pair'], 
            timeframe=self.informative_timeframe
        )
        
        if not informative.empty:
            # Higher timeframe trend indicators
            informative['ema_short'] = ta.EMA(informative, timeperiod=self.ema_short.value)
            informative['ema_long'] = ta.EMA(informative, timeperiod=self.ema_long.value)
            informative['rsi'] = ta.RSI(informative, timeperiod=self.rsi_period.value)
            informative['adx'] = ta.ADX(informative, timeperiod=self.adx_period.value)
            
            # Higher timeframe bias: 1 = bullish, -1 = bearish, 0 = neutral
            informative['htf_bias'] = np.where(
                (informative['ema_short'] > informative['ema_long']) & 
                (informative['rsi'] > 50) & 
                (informative['adx'] > self.adx_threshold.value),
                1,
                np.where(
                    (informative['ema_short'] < informative['ema_long']) & 
                    (informative['rsi'] < 50) & 
                    (informative['adx'] > self.adx_threshold.value),
                    -1,
                    0
                )
            )
            
            # Merge informative data
            dataframe = self.merge_informative_pair(dataframe, informative, self.informative_timeframe)
        
        # Williams Fractals
        dataframe['fractal_up'] = self._williams_fractal_up(dataframe, self.fractal_period.value)
        dataframe['fractal_down'] = self._williams_fractal_down(dataframe, self.fractal_period.value)
        
        # EMAs for current timeframe
        dataframe['ema_short'] = ta.EMA(dataframe, timeperiod=self.ema_short.value)
        dataframe['ema_long'] = ta.EMA(dataframe, timeperiod=self.ema_long.value)
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period.value)
        
        # ADX
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=self.adx_period.value)
        dataframe['di_plus'] = ta.PLUS_DI(dataframe, timeperiod=self.adx_period.value)
        dataframe['di_minus'] = ta.MINUS_DI(dataframe, timeperiod=self.adx_period.value)
        
        # ATR for dynamic stops
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period.value)
        
        # Alligator Indicator (Bill Williams)
        dataframe['alligator_jaw'] = ta.EMA(dataframe['close'].shift(8), timeperiod=13)
        dataframe['alligator_teeth'] = ta.EMA(dataframe['close'].shift(5), timeperiod=8)
        dataframe['alligator_lips'] = ta.EMA(dataframe['close'].shift(3), timeperiod=5)
        
        # Alligator state: 1 = awake (trending), 0 = sleeping (ranging)
        dataframe['alligator_awake'] = np.where(
            (dataframe['alligator_jaw'] > dataframe['alligator_teeth']) & 
            (dataframe['alligator_teeth'] > dataframe['alligator_lips']),
            1,  # Bullish trend
            np.where(
                (dataframe['alligator_jaw'] < dataframe['alligator_teeth']) & 
                (dataframe['alligator_teeth'] < dataframe['alligator_lips']),
                -1,  # Bearish trend
                0  # Sleeping
            )
        )
        
        # Volume indicators
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
        
        # Fractal-based support/resistance levels
        dataframe['resistance'] = dataframe['fractal_up'].rolling(window=20).max()
        dataframe['support'] = dataframe['fractal_down'].rolling(window=20).min()
        
        # Distance from key levels (as percentage)
        dataframe['dist_from_resistance'] = (dataframe['resistance'] - dataframe['close']) / dataframe['close'] * 100
        dataframe['dist_from_support'] = (dataframe['close'] - dataframe['support']) / dataframe['close'] * 100
        
        return dataframe
    
    def _williams_fractal_up(self, df: DataFrame, period: int = 5) -> DataFrame:
        """Calculate Williams Fractal Up (bearish reversal)"""
        high = df['high']
        # Fractal up: high[n-2] < high[n] > high[n+2] and high[n-1] < high[n] and high[n+1] < high[n]
        shift = period // 2
        return np.where(
            (high.shift(shift*2) < high) & 
            (high.shift(shift) < high) & 
            (high.shift(-shift) < high) & 
            (high.shift(-shift*2) < high),
            high,
            np.nan
        )
    
    def _williams_fractal_down(self, df: DataFrame, period: int = 5) -> DataFrame:
        """Calculate Williams Fractal Down (bullish reversal)"""
        low = df['low']
        shift = period // 2
        return np.where(
            (low.shift(shift*2) > low) & 
            (low.shift(shift) > low) & 
            (low.shift(-shift) > low) & 
            (low.shift(-shift*2) > low),
            low,
            np.nan
        )
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Define entry conditions"""
        
        # Long entry conditions
        long_conditions = [
            # Higher timeframe bias is bullish
            (dataframe[f'htf_bias_{self.informative_timeframe}'] == 1),
            
            # Current timeframe: price above EMAs
            (dataframe['close'] > dataframe['ema_short']),
            (dataframe['ema_short'] > dataframe['ema_long']),
            
            # Alligator awake and bullish
            (dataframe['alligator_awake'] == 1),
            
            # Fractal down (bullish reversal) formed recently
            (dataframe['fractal_down'].notna() & dataframe['fractal_down'].shift(1).isna()),
            
            # RSI not overbought
            (dataframe['rsi'] < self.rsi_overbought.value),
            
            # ADX showing trend strength
            (dataframe['adx'] > self.adx_threshold.value),
            
            # Volume confirmation
            (dataframe['volume_ratio'] > 1.0),
            
            # DI+ > DI- for bullish momentum
            (dataframe['di_plus'] > dataframe['di_minus']),
        ]
        
        dataframe.loc[
            reduce(lambda x, y: x & y, long_conditions),
            'enter_long'] = 1
        
        # Short entry conditions
        short_conditions = [
            # Higher timeframe bias is bearish
            (dataframe[f'htf_bias_{self.informative_timeframe}'] == -1),
            
            # Current timeframe: price below EMAs
            (dataframe['close'] < dataframe['ema_short']),
            (dataframe['ema_short'] < dataframe['ema_long']),
            
            # Alligator awake and bearish
            (dataframe['alligator_awake'] == -1),
            
            # Fractal up (bearish reversal) formed recently
            (dataframe['fractal_up'].notna() & dataframe['fractal_up'].shift(1).isna()),
            
            # RSI not oversold
            (dataframe['rsi'] > self.rsi_oversold.value),
            
            # ADX showing trend strength
            (dataframe['adx'] > self.adx_threshold.value),
            
            # Volume confirmation
            (dataframe['volume_ratio'] > 1.0),
            
            # DI- > DI+ for bearish momentum
            (dataframe['di_minus'] > dataframe['di_plus']),
        ]
        
        dataframe.loc[
            reduce(lambda x, y: x & y, short_conditions),
            'enter_short'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Define exit conditions"""
        
        # Long exit conditions
        long_exit_conditions = [
            # HTF bias flipped to bearish
            (dataframe[f'htf_bias_{self.informative_timeframe}'] == -1),
            
            # OR Alligator sleeping/bearish
            (dataframe['alligator_awake'] <= 0),
            
            # OR Fractal up formed (bearish reversal)
            (dataframe['fractal_up'].notna() & dataframe['fractal_up'].shift(1).isna()),
            
            # OR RSI overbought
            (dataframe['rsi'] > self.rsi_overbought.value),
            
            # OR DI- crossed above DI+
            (dataframe['di_minus'] > dataframe['di_plus']),
        ]
        
        dataframe.loc[
            reduce(lambda x, y: x | y, long_exit_conditions),
            'exit_long'] = 1
        
        # Short exit conditions
        short_exit_conditions = [
            # HTF bias flipped to bullish
            (dataframe[f'htf_bias_{self.informative_timeframe}'] == 1),
            
            # OR Alligator sleeping/bullish
            (dataframe['alligator_awake'] >= 0),
            
            # OR Fractal down formed (bullish reversal)
            (dataframe['fractal_down'].notna() & dataframe['fractal_down'].shift(1).isna()),
            
            # OR RSI oversold
            (dataframe['rsi'] < self.rsi_oversold.value),
            
            # OR DI+ crossed above DI-
            (dataframe['di_plus'] > dataframe['di_minus']),
        ]
        
        dataframe.loc[
            reduce(lambda x, y: x | y, short_exit_conditions),
            'exit_short'] = 1
        
        return dataframe
    
    def leverage(self, pair: str, current_time: 'datetime', current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str],
                 side: str, **kwargs) -> float:
        """Dynamic leverage based on volatility"""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Lower leverage in high volatility
        atr_pct = last_candle['atr'] / last_candle['close'] * 100
        if atr_pct > 3:
            return 3.0
        elif atr_pct > 2:
            return 5.0
        else:
            return min(max_leverage, 10.0)
    
    def custom_stake_amount(self, pair: str, current_time: 'datetime', current_rate: float,
                            proposed_stake: float, min_stake: Optional[float],
                            max_stake: float, leverage: float, entry_tag: Optional[str],
                            side: str, **kwargs) -> float:
        """Dynamic position sizing based on volatility and account risk"""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Risk 1% of stake per trade, adjusted for ATR
        atr_value = last_candle['atr']
        stop_distance = atr_value * self.atr_multiplier.value
        
        # Calculate position size based on stop distance
        risk_per_trade = proposed_stake * 0.01  # 1% risk
        position_size = risk_per_trade / stop_distance * current_rate
        
        # Apply leverage
        position_size = position_size * leverage
        
        # Clamp to min/max
        return max(min_stake or 0, min(position_size, max_stake))
    
    def version(self) -> str:
        return "1.0.0"


# Need to import reduce
from functools import reduce
from datetime import datetime