from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.core.security import get_current_user, verify_group_membership
from app.db.supabase import supabase
from app.schemas.cohort import CohortRead, CohortCreate
from app.services.finance import get_live_prices
from collections import defaultdict
from app.services.colors import uuid_to_color
from app.services.logger import sys_logger
from app.services.stock_history import get_stock_history
router = APIRouter()

@router.get("/", response_model=Optional[List[CohortRead]])
def get_active_cohorts(group_id: str, current_user = Depends(get_current_user)):
    """
    Fetches all the OPEN cohorts for a specified group
    """
    try:
        verify_group_membership(current_user.id, group_id)
        response = supabase.table("cohorts").select("*").eq("group_id", group_id).eq("status", "OPEN").order("created_at").execute()
        return response.data
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/{cohort_id}")
def get_cohort_details(group_id: str, cohort_id: str, current_user = Depends(get_current_user)):
    try:
        verify_group_membership(user_id=current_user.id, group_id=group_id)

        cohort_res = supabase.table("cohorts").select("month_year, status").eq("id", cohort_id).single().execute()
        group_res  = supabase.table("group_members").select("user_id, profiles(display_name)").eq("group_id", group_id).execute()
        ledger_res = supabase.table("ledger").select("id, amount, transaction_type, profiles(display_name, id)").eq("cohort_id", cohort_id).execute()
        trades_res = supabase.table("trades").select("*").eq("cohort_id", cohort_id).execute()

        open_trades   = [t for t in trades_res.data if t["status"] == "OPEN"]
        closed_trades = [t for t in trades_res.data if t["status"] == "CLOSED"]

        realized_pnl = sum(
            float(t["quantity"]) * (float(t["sell_price"]) - float(t["buy_price"]))
            for t in closed_trades
        )
        ledger = ledger_res.data
        total_pool        = sum( float(tx["amount"]) for tx in ledger if tx['transaction_type'] == "DEPOSIT"      )
        withdrawn_amount  = sum( float(tx["amount"]) for tx in ledger if tx['transaction_type'] == "WITHDRAWAL"   )
        rollover_amount   = sum( float(tx["amount"]) for tx in ledger if "ROLL_FORWARD" in tx['transaction_type'] )
        actual_total_pool = total_pool + rollover_amount
        invested          = sum(float(trade["quantity"]) * float(trade["buy_price"]) for trade in open_trades)
        available_cash    = actual_total_pool - invested - withdrawn_amount

        colors = ["#3b82f6", "#a855f7", "#ec4899", "#f59e0b", "#10b981"]
        formatted_contributions = []

        for idx, tx in enumerate(ledger_res.data):
            if tx['transaction_type'] == "DEPOSIT" or "ROLL_FORWARD" in tx["transaction_type"]:
                amount    = float(tx["amount"])
                share_pct = round((amount / total_pool * 100), 2) if total_pool > 0 else 0

                formatted_contributions.append({
                    "id"     : tx["id"],
                    "user_id": tx["profiles"]["id"],
                    "name"   : tx["profiles"]["display_name"],
                    "amount" : amount,
                    "share"  : share_pct,
                    "color"  : colors[idx % len(colors)]
                })

        grouped_contributions = defaultdict(lambda: {
                                                "user_id": "",
                                                "name"   : "",
                                                "amount" : 0,
                                            })
        for item in formatted_contributions:
            user      = grouped_contributions[item["user_id"]]

            user["user_id"] = item["user_id"]
            user["name"]    = item["name"]
            user["amount"] += round(item["amount"], 2)

        formatted_contributions = list(grouped_contributions.values())

        for item in formatted_contributions:
            amount        = item["amount"]
            item['share'] = round((amount / actual_total_pool * 100), 2) if actual_total_pool > 0 else 0
            item['color'] = uuid_to_color(item['user_id'])

        formatted_holdings = []
        live_prices        = []
        sector_exposure    = {}

        if trades_res.data:
            tickers = [t["ticker_symbol"] for t in trades_res.data]
            live_prices = get_live_prices(tickers)

        for trade in trades_res.data:
            ticker = trade["ticker_symbol"]
            formatted_holdings.append({
                "ticker"    : ticker,
                "id"        : trade["id"],
                "qty"       : float(trade["quantity"]),
                "avg"       : float(trade["buy_price"]),
                "current"   : float(live_prices[trade["ticker_symbol"]]),
                "buy_date"  : trade["buy_date"],
                "status"    : trade["status"],
                "sell_date" : trade["sell_date"] if trade["status"] == "CLOSED" else None,
                "sell_price": float(trade["sell_price"]) if trade["status"] == "CLOSED" else None,
                "other_pnl" : trade["other_pnl"],
                "history"   : get_stock_history(ticker, trade["buy_date"], trade["buy_price"])
            })
            current_val = float(trade["quantity"]) * float(trade["buy_price"])
            if trade["status"] == "OPEN":
                sector = trade['sector']
                if sector not in sector_exposure:
                    sector_exposure[sector] = 0.0
                sector_exposure[sector] += current_val

        formatted_exposure = []
        ring_colors = ["#3b82f6", "#a855f7", "#ec4899", "#f59e0b", "#10b981", "#ef4444"]

        for idx, (sec, val) in enumerate(sorted(sector_exposure.items(), key=lambda x: x[1], reverse=True)):
            pct = (val / invested * 100) if invested > 0 else 0
            formatted_exposure.append({
                "name": sec,
                "value": val,
                "percentage": round(pct, 1),
                "color": ring_colors[idx % len(ring_colors)]
            })

        return {
            "id"    : cohort_id,
            "name"  : cohort_res.data["month_year"],
            "status": cohort_res.data["status"],
            "stats" : {
                "total_pool"    : total_pool,
                "invested"      : invested,
                "available_cash": available_cash
            },
            "members"        : group_res.data,
            "contributions"  : formatted_contributions,
            "holdings"       : formatted_holdings,
            "sector_exposure": formatted_exposure
        }

    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Optional[CohortRead])
def create_cohort(cohort: CohortCreate, current_user = Depends(get_current_user)):
    """
    Open a new monthly cohort (e.g., APR_2026)
    """
    try:
        verify_group_membership(current_user.id, str(cohort.group_id))
        data_to_insert = cohort.model_dump(mode='json')
        response       = supabase.table("cohorts").insert(data_to_insert).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create cohort")

        return response.data[0]
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=Optional[List[CohortRead]])
def get_historical_cohorts(group_id: str, current_user = Depends(get_current_user)):
    """
    Fetches all CLOSED cohorts for a specified group (The Archive).
    """
    try:
        verify_group_membership(current_user.id, group_id)

        response = supabase.table("cohorts").select("*").eq("group_id", group_id).eq("status", "CLOSED").order("created_at", desc=True).execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))