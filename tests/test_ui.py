from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_ui_root_endpoint_serves_html():
    """
    Verifies that GET / serves the Lumina Noir index.html page.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Zomato AI Concierge" in response.text
    assert "static/app.js" in response.text


def test_ui_static_js_asset_served():
    """
    Verifies that GET /static/app.js returns the JavaScript client code.
    """
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("content-type", "").lower()
    assert "DOMContentLoaded" in response.text
