import yfinance as yf
from typing import List, Dict

def get_live_prices(tickers: List[str]) -> Dict[str, float]:
    """
    Takes a list of ticker symbols and returns a dictionary
    mapping each ticker to its latest closing price.
    """
    if not tickers:
        return {}

    live_prices = {}
    for ticker in set(tickers):
        try:
            stock = yf.Ticker(ticker)
            hist  = stock.history(period="1d")
            if not hist.empty:
                latest_price        = float(hist['Close'].iloc[-1])
                live_prices[ticker] = round(latest_price, 2)
            else:
                live_prices[ticker] = 0.0
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            live_prices = 0.0
    return live_prices