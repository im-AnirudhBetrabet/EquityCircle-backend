from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.db.supabase import supabase
from app.schemas import TradeUpdate
from app.schemas.trade import TradeCreate, TradeRead
from app.services.finance import get_live_prices
from app.core.security import get_current_user, verify_group_membership

router = APIRouter()

@router.post("/", response_model=TradeRead)
def record_create(trade: TradeCreate, current_user = Depends(get_current_user)):
    """
    Logs a new stock purchase into a specific cohort
    """
    try:
        data_to_insert = trade.model_dump(mode='json')
        response       = supabase.table("trades").insert(data_to_insert).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to record trade")

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/{cohort_id}")
def get_active_trades(cohort_id: str, current_user = Depends(get_current_user)):
    """
    Fetches all OPEN trades for a cohort AND appends the live market price.
    """
    try:
        response = supabase.table("trades").select("*").eq("cohort_id", cohort_id).eq("status", "OPEN").execute()
        trades   = response.data

        if not trades:
            return []

        tickers     = [trade["ticker_symbol"] for trade in trades]
        live_prices = get_live_prices(tickers)

        for trade in trades:
            ticker = trade["ticker_symbol"]
            trade["current_price"] = live_prices.get(ticker, 0.0)

            total_invested             = trade["buy_price"] * trade["quantity"]
            current_value              = trade["current_price"] * trade["quantity"]
            trade["unrealized_profit"] = round(current_value - total_invested, 2)

        return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{trade_id}/close", response_model=TradeRead)
def close_trade(trade_id: str, update_data: TradeUpdate):
    """
    Executes a sell. Marks the trade as CLOSED and locks in the sell price.
    """
    try:
        data_to_update = {
            "status"    : "CLOSED",
            "sell_price": update_data.sell_price,
            "sell_date" : update_data.sell_date.isoformat()
        }

        response = supabase.table("trades").update(data_to_update).eq("id", trade_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Trade not found")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))