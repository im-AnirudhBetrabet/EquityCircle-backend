from fastapi import APIRouter, HTTPException
from typing import List
from app.db.supabase import supabase
from app.schemas.ledger import LedgerCreate, LedgerRead
from app.services.math_engine import calculate_equity_splits


router = APIRouter()

@router.post("/", response_model=LedgerRead)
def record_transaction(transaction: LedgerCreate):
    """
    Record a new capital movement (DEPOSIT, WITHDRAWAL, ROLL_FORWARD, INTEREST).
    """
    try:
        data_to_insert = transaction.model_dump(mode="json")
        response       = supabase.table("ledger").insert(data_to_insert).execute()
        print(response)

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to record transaction")

        return response.data[0]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/splits/{cohort_id}")
def get_cohort_splits(cohort_id: str):
    """
    Fetches all transactions for a cohort and dynamically calculates who owns what.
    """
    try:
        response = supabase.table("ledger").select("*").eq("cohort_id", cohort_id).execute()

        entries = response.data

        if not entries:
            return {
                "total_pool"   : 0.0,
                "member_splits": {}
            }

        return calculate_equity_splits(entries)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
