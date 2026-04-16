from typing import List, Dict

def calculate_equity_splits(ledger_entries: List[dict]) -> Dict[str, dict]:
    """
    Takes a raw list of ledger transactions for a cohort and dynamically
    calculates the total pool and the exact equity percentage for each member.
    """
    user_totals = {}
    total_pool  = 0.0

    for entry in ledger_entries:
        user_id = str(entry["user_id"])
        amount  = float(entry["amount"])

        if user_id not in user_totals:
            user_totals[user_id] = 0.0

        user_totals[user_id] += amount
        total_pool           += amount

    splits = {}

    for uid, amount in user_totals.items():
        percentage = ( amount / total_pool ) if total_pool > 0 else 0.0

        splits[uid] = {
            "invested_amount"  : round(amount, 2),
            "equity_percentage": round(percentage, 4)
        }

    return {
        "total_pool"   : round(total_pool, 2),
        "member_splits": splits
    }