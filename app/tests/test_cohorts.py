from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import get_current_user
from unittest.mock import MagicMock

client = TestClient(app)

TEST_GROUP_ID = settings.TEST_GROUP_ID

mock_user = MagicMock()
mock_user.id = 'test-user-uuid'
mock_user.user_id = {
    "group_id": TEST_GROUP_ID
}

async def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

def test_create_and_fetch_cohort():
    """
    Tests the full lifecycle of a cohort: Creation -> Fetching
    """
    new_cohort_data = {
        "month_year": "MAY_2026",
        "status"    : "OPEN",
        "group_id"  : TEST_GROUP_ID
    }

    response = client.post(f"{settings.API_V1_STR}/cohorts/", json=new_cohort_data)
    assert response.status_code == 200

    created_cohort = response.json()

    assert created_cohort["month_year"] == "MAY_2026"
    assert created_cohort["status"]     == "OPEN"
    assert "id" in created_cohort

    fetch_response = client.get(f"{settings.API_V1_STR}/cohorts/?group_id={TEST_GROUP_ID}")
    assert fetch_response.status_code == 200

    cohorts_list = fetch_response.json()
    assert len(cohorts_list) > 0

    month_years = [c["month_year"] for c in cohorts_list]
    assert "MAY_2026" in month_years