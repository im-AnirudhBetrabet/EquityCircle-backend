from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import uuid

from app.services.math_engine import calculate_equity_splits

client = TestClient(app)

TEST_GROUP_ID  = settings.TEST_GROUP_ID
TEST_COHORT_ID = settings.TEST_COHORT_ID

USER_A = str(uuid.uuid4())
USER_B = str(uuid.uuid4())
USER_C = str(uuid.uuid4())

def test_ledger_math_engine():
    """
    Simulate deposits and ensure the FastAPI math engine
    calculates the exact equity percentages.
    """

    mock_db_entries = [
        {"user_id": USER_A, "amount": 3400.00},
        {"user_id": USER_B, "amount": 3300.00},
        {"user_id": USER_C, "amount": 3300.00}
    ]
    result = calculate_equity_splits(mock_db_entries)

    assert result["total_pool"] == 10000.00

    # 2. Verify Exact Equity Percentages
    splits = result["member_splits"]
    assert splits[USER_A]["equity_percentage"] == 0.3400
    assert splits[USER_B]["equity_percentage"] == 0.3300
    assert splits[USER_C]["equity_percentage"] == 0.3300