from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

TEST_COHORT_ID = settings.TEST_COHORT_ID

def test_record_and_fetch_trade():
    new_trade = {
        "ticker_symbol": "RELIANCE.NS",
        "quantity"     : 2,
        "buy_price"    : 2900.00,
        "cohort_id"    : TEST_COHORT_ID
    }

    post_response = client.post(f"{settings.API_V1_STR}/trades/", json=new_trade)

    assert post_response.status_code == 200

    get_response = client.get(f"{settings.API_V1_STR}/trades/active/{TEST_COHORT_ID}")
    assert get_response.status_code == 200

    active_trades = get_response.json()
    assert len(active_trades) > 0

    reliance_trade = next(t for t in active_trades if t["ticker_symbol"] == "RELIANCE.NS")
    assert "current_price"     in reliance_trade
    assert "unrealized_profit" in reliance_trade
    assert reliance_trade["current_price"] > 0

