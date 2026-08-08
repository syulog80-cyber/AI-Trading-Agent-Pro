from trading.binance import BinanceConnector
from trading.indicators import IndicatorEngine
from trading.ai_predictor import AIPredictor
from trading.multi_timeframe import MultiTimeframeAnalyzer
from trading.opportunity_engine import OpportunityEngine
from trading.scanner import MarketScanner


class TradingController:

    def __init__(self):

        self.exchange = BinanceConnector()
        self.indicators = IndicatorEngine()
        self.predictor = AIPredictor()
        self.multi_tf = MultiTimeframeAnalyzer(self)
        self.opportunity = OpportunityEngine()
        self.scanner = MarketScanner(self)

    # ===========================================
    # Load Market
    # ===========================================

    def load_market(
        self,
        symbol,
        timeframe="1h",
        limit=500
    ):
        candles = self.exchange.get_candles(
            symbol,
            timeframe,
            limit
        )
        return self.indicators.calculate(candles)

    # ===========================================
    # Analyze Market
    # ===========================================

    def analyze_market(
        self,
        symbol,
        timeframe="1h",
        limit=500
    ):
        candles = self.load_market(
            symbol,
            timeframe,
            limit
        )

        prediction = self.predictor.predict(candles)

        return {
            "candles": candles,
            "prediction": prediction,
            "candle_index": len(candles) - 1,
            "candle_time": candles.index[-1]
        }

    # ===========================================
    # Multi-Timeframe Analysis
    # ===========================================

    def analyze_multi_timeframe(
        self,
        symbol,
        timeframes=("15m", "1h", "4h", "1d")
    ):
        analyses = self.multi_tf.analyze(symbol, timeframes=timeframes)
        alignment = self.multi_tf.alignment(analyses)
        signal = self.multi_tf.final_signal(analyses)

        return {
            "symbol": symbol,
            "analyses": analyses,
            "alignment": alignment,
            "signal": signal,
        }

    # ===========================================
    # Trade Plan
    # ===========================================

    def get_trade_plan(self, symbol, timeframe="1h"):
        market = self.analyze_market(symbol, timeframe=timeframe)
        prediction = market["prediction"]
        mtf = self.analyze_multi_timeframe(symbol)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "prediction": prediction,
            "signal": mtf["signal"],
            "alignment": mtf["alignment"],
            "analyses": mtf["analyses"],
            "entry_price": prediction.get("entry_price"),
            "stop_loss": prediction.get("stop_loss"),
            "take_profit": prediction.get("take_profit"),
            "risk_reward": prediction.get("risk_reward"),
            "position_size": prediction.get("position_size"),
            "position_value": prediction.get("position_value"),
            "confidence": prediction.get("confidence", 0),
            "grade": prediction.get("grade", "D"),
            "strategy": prediction.get("strategy", "Wait"),
            "tradable": bool(prediction.get("tradable", False)) and mtf["signal"] != "HOLD",
        }

    # ===========================================
    # Market Scanner
    # ===========================================

    def scan_market(
        self,
        symbols,
        timeframe="1h",
        workers=8,
        min_confidence=70.0,
        allowed_grades=("A+", "A", "B")
    ):
        return self.scanner.scan(
            symbols=symbols,
            timeframe=timeframe,
            workers=workers,
            min_confidence=min_confidence,
            allowed_grades=allowed_grades,
        )

    # ===========================================
    # Current Price
    # ===========================================

    def get_price(self, symbol):
        return self.exchange.get_price(symbol)

    # ===========================================
    # Symbols
    # ===========================================

    def get_symbols(self):
        return self.exchange.get_symbols()
