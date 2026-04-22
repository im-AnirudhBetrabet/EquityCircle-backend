from typing import List, Dict

def calculate_equity_splits(ledger_entries: List[dict]) -> Dict[str, dict]:
    """
    Takes a raw list of ledger transactions and dynamically calculates
    the total pool and exact equity percentage, respecting transaction types.
    """
    user_totals = {}
    total_pool  = 0.0

    for entry in ledger_entries:
        user_id  = str(entry["user_id"])
        amount   = float(entry["amount"])
        txn_type = entry.get("transaction_type", "DEPOSIT").upper()

        if user_id not in user_totals:
            user_totals[user_id] = 0.0

        # DOUBLE ENTRY LOGIC: Add money flowing in, subtract money flowing out
        if txn_type in ["DEPOSIT", "ROLL_FORWARD", "INTEREST"]:
            user_totals[user_id] += amount
            total_pool           += amount
        elif txn_type == "WITHDRAWAL":
            user_totals[user_id] -= amount
            total_pool           -= amount

    splits = {}

    for uid, amount in user_totals.items():
        # Prevent negative percentages if a user fully withdraws everything
        if amount <= 0:
            splits[uid] = {
                "invested_amount": 0.0,
                "equity_percentage": 0.0
            }
            continue

        percentage = (amount / total_pool) if total_pool > 0 else 0.0

        splits[uid] = {
            "invested_amount"  : round(amount, 2),
            "equity_percentage": round(percentage, 4)
        }

    return {
        "total_pool"   : round(max(total_pool, 0.0), 2),
        "member_splits": splits
    }