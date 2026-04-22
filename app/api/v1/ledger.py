from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import supabase
from app.schemas.ledger import LedgerCreate, LedgerRead, CohortSettlementPayload
from app.services.math_engine import calculate_equity_splits
from app.core.security import get_current_user, verify_group_membership


router = APIRouter()

@router.post("/", response_model=LedgerRead)
def record_transaction(transaction: LedgerCreate, current_user = Depends(get_current_user)):
    """
    Record a new capital movement (DEPOSIT, WITHDRAWAL, ROLL_FORWARD, INTEREST).
    """
    try:
        verify_group_membership(current_user.id, str(transaction.group_id))
        data_to_insert = transaction.model_dump(mode="json")
        response       = supabase.table("ledger").insert(data_to_insert).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to record transaction")

        return response.data[0]
    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/splits/{cohort_id}")
def get_cohort_splits(cohort_id: str, current_user = Depends(get_current_user)):
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
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/{cohort_id}/settle")
def settle_cohort(group_id: str, cohort_id, payload: CohortSettlementPayload, current_user = Depends(get_current_user)):
    try:
        current_user_id = current_user.id
        verify_group_membership(current_user_id, group_id)

        ledger_inserts = []
        settlements = payload.settlements
        for item in settlements:
            total_value = item.principal_amount + item.profit_amount

            if total_value > 0:
                ledger_inserts.append({
                    "group_id"        : str(group_id),
                    "cohort_id"       : str(cohort_id),
                    "user_id"         : str(item.user_id),
                    "amount"          : item.principal_amount,
                    "transaction_type": "WITHDRAWAL"
                })

            if item.profit_amount > 0:
                ledger_inserts.append({
                    "group_id"        : str(group_id),
                    "cohort_id"       : str(cohort_id),
                    "user_id"         : str(item.user_id),
                    "amount"          : item.profit_amount,
                    "transaction_type": "INTEREST"
                })

            if item.transaction_type == "ROLLOVER_ALL" and item.target_cohort_id:
                ledger_inserts.append({
                    "group_id"        : str(group_id),
                    "cohort_id"       : str(item.target_cohort_id),
                    "user_id"         : str(item.user_id),
                    "amount"          : total_value,
                    "transaction_type": "ROLL_FORWARD"
                })

            elif item.transaction_type == "ROLLOVER_PRINCIPAL" and item.target_cohort_id:
                ledger_inserts.append({
                    "group_id"        : str(group_id),
                    "cohort_id"       : str(item.target_cohort_id),
                    "user_id"         : str(item.user_id),
                    "amount"          : item.principal_amount,
                    "transaction_type": "ROLL_FORWARD"
                })
        if ledger_inserts:
            supabase.table("ledger").insert(ledger_inserts).execute()

        supabase.table("cohorts").update({"status": "CLOSED"}).eq("id", cohort_id).execute()

        return {
            "status"   : "success",
            "processed": len(payload.settlements)
        }

    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(detail=str(e), status_code=500)

