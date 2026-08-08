from trading.binance import BinanceConnector
from trading.indicators import IndicatorEngine
from trading.ai_predictor import AIPredictor
from trading.multi_timeframe import MultiTimeframeAnalyzer
from trading.opportunity_engine import OpportunityEngine


class TradingController:

    def __init__(self):

        self.exchange = BinanceConnector()

        self.indicators = IndicatorEngine()

        self.predictor = AIPredictor()

        self.multi_tf = MultiTimeframeAnalyzer(self)

        self.opportunity = OpportunityEngine()

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

        candles = self.indicators.calculate(

            candles

        )

        return candles

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

        prediction = self.predictor.predict(

            candles

        )

        return {

            "candles": candles,

            "prediction": prediction,

            "candle_index": len(candles)-1,

            "candle_time": candles.index[-1]

        }

    # ===========================================
    # Current Price
    # ===========================================

    def get_price(self,symbol):

        return self.exchange.get_price(symbol)

    # ===========================================
    # Symbols
    # ===========================================

    def get_symbols(self):

        return self.exchange.get_symbols()