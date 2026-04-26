import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from app.services.logger import sys_logger
def get_stock_history(ticker: str, iso_date: str, buy_price: float):
     try:
         from_date = (datetime.fromisoformat(iso_date) - timedelta(days=10)).strftime("%Y-%m-%d")
         to_date   = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
         sys_logger.info(f"Fetching prices for {ticker} from {from_date} to {to_date}")
         data      = yf.download(progress=False, tickers=ticker, start=from_date, end=to_date)
         if data.empty:
             return {"data": []}

         if isinstance(data.columns, pd.MultiIndex):
             data.columns = data.columns.droplevel(1)

         data = data[['Close']].copy()

         data.reset_index(inplace=True)

         data['pnl'] = data['Close'] - buy_price
         result = []
         for _, row in data.iterrows():
             result.append({
                 "date" : row['Date'].strftime("%Y-%m-%d"),
                 "price": round(row['Close'], 2),
                 "pnl"  : round(row['pnl'], 2),
             })

         return {"data": result}

     except Exception as e:
         sys_logger.error(f"Unable to fetch stock history for {ticker} due to error: {str(e)}")