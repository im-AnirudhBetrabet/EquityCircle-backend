from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

@patch("app.api.v1.auth.supabase")
def test_signup_without_group(mock_supabase):
    """
    Test that a user can successfully hit the signup endpoint
    without providing a group_id.
    """
    mock_user          = MagicMock()
    mock_user.id       = "test-uuid-1234"
    mock_response      = MagicMock()
    mock_response.user = mock_user

    mock_supabase.auth.sign_up.return_value = mock_response

    payload = {
        "display_name": "Free Agent",
        "password"    : "securepassword123",
        "email"       : "freeagent@example.com"
    }

    response = client.post(f"{settings.API_V1_STR}/auth/signup", json=payload)

    assert response.status_code       == 200
    assert response.json()["message"] == "User created successfully"
    assert response.json()["user_id"] == "test-uuid-1234"

    mock_supabase.auth.sign_up.assert_called_once()
    called_args = mock_supabase.auth.sign_up.call_args[0][0]
    assert "group_id" not in called_args["options"]["data"]
