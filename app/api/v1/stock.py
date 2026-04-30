from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

from app.schemas.stock import StockInfoResponse
from app.services.logger import sys_logger

router = APIRouter()
@router.get("/info", response_model=StockInfoResponse)
def get_stock_history(ticker: str, buy_price: float, iso_from_date: str, iso_to_date: str = None, current_user = Depends(get_current_user)):
    print(ticker, buy_price, iso_to_date, iso_from_date)
    """
    Get the stock prices for the specified stock.
    :param ticker: The ticker of the stock for which the data is needed.
    :param buy_price: The price at which the stock was brought.
    :param iso_from_date: The date from which the stock price is required.
    :param iso_to_date: The date to which the stock price is required. If None, the current date is used.
    :return: Stock price data
    """
    try:
        from_date = (datetime.fromisoformat(iso_from_date) - timedelta(days=10)).strftime("%Y-%m-%d")
        to_date   = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") if iso_to_date is None else (datetime.fromisoformat(iso_to_date) + timedelta(days=4)).strftime("%Y-%m-%d")
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
        raise HTTPException(status_code=500, detail=f"Unable to fetch stock history for {ticker} due to error: {str(e)}")