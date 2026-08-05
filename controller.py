
from trading.binance import BinanceConnector
from trading.indicators import IndicatorEngine
from trading.ai_predictor import AIPredictor
from trading.multi_timeframe import MultiTimeframeAnalyzer
from trading.opportunity_engine import OpportunityEngine


class TradingController:
    """AI Trading Agent Pro v2 Core Controller"""

    def __init__(self):
        self.exchange = BinanceConnector()
        self.indicators = IndicatorEngine()
        self.predictor = AIPredictor()
        self.multi_tf = MultiTimeframeAnalyzer(self)
        self.opportunity = OpportunityEngine()

    def test_connection(self):
        return self.exchange.test_connection()

    def get_symbols(self):
        return self.exchange.get_symbols()

    def get_price(self, symbol):
        return self.exchange.get_price(symbol)

    def load_market(self, symbol, timeframe="1h", limit=500):
        candles = self.exchange.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )

        if candles is None or candles.empty:
            raise ValueError(f"{symbol}: No market data.")

        return self.indicators.calculate(candles)

    def analyze_market(self, symbol, timeframe="1h", limit=500):
        candles = self.load_market(symbol, timeframe, limit)
        prediction = self.predictor.predict(candles)

        return {
            "candles": candles,
            "prediction": prediction,
            "candle_index": len(candles)-1,
            "candle_time": candles.index[-1]
        }

    def analyze_multi_timeframe(self, symbol,
                                timeframes=("15m","1h","4h","1d")):

        analyses = self.multi_tf.analyze(
            symbol,
            timeframes=timeframes
        )

        alignment = self.multi_tf.alignment(analyses)

        final_signal = self.multi_tf.final_signal(analyses)

        return {
            "analysis": analyses,
            "alignment": alignment,
            "final_signal": final_signal
        }
