from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

# Create a test client using your FastAPI app
client = TestClient(app)


def test_health_check_endpoint():
    """
    Test that the root health check endpoint returns a 200 OK
    and the correct JSON structure.
    """
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"]  == "online"
    assert data["project"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION