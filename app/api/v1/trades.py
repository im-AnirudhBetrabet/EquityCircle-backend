from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.db.supabase import supabase
from app.schemas import TradeUpdate
from app.schemas.trade import TradeCreate, TradeRead, TradeAdjustment
from app.services.finance import get_live_prices
from app.core.security import get_current_user, verify_group_membership
from app.services.logger import sys_logger
import yfinance as yf
from typing import Optional
router = APIRouter()

@router.post("/", response_model=Optional[TradeRead])
def record_create(trade: TradeCreate, current_user = Depends(get_current_user)):
    """
    Logs a new stock purchase into a specific cohort
    """
    try:
        data_to_insert = trade.model_dump(mode='json')
        try:
            ticker_info = yf.Ticker(trade.ticker_symbol).info
            data_to_insert["sector"] = ticker_info.get("sector", "Other")
        except Exception as e:
            sys_logger.warning(f"Could not fetch sector for {trade.ticker_symbol}: {e}")
            data_to_insert["sector"] = "Other"

        response       = supabase.table("trades").insert(data_to_insert).execute()

        if not response.data:
            sys_logger.error(f"Failed to record trade {response.error_message}")
            raise HTTPException(status_code=400, detail="Failed to record trade")

        return response.data[0]
    except Exception as e:
        sys_logger.error(e)
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
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{trade_id}/close", response_model=Optional[TradeRead])
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
            sys_logger.error(f"Trade not found: {response.error_message}")
            raise HTTPException(status_code=404, detail="Trade not found")
        return response.data[0]
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{trade_id}/adjust")
def adjust_trade_pnl(trade_id: str, payload: TradeAdjustment):
    try:
        trade_res = supabase.table("trades").select("other_pnl").eq("id", trade_id).single().execute()
        current_other = float(trade_res.data.get("other_pnl") or 0)

        new_total = current_other + payload.other_pnl_amount

        adjust_response = supabase.table("trades").update({ "other_pnl": new_total}).eq("id", trade_id).execute()

        return adjust_response.data[0]
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))
