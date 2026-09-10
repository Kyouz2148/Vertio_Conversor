import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Conversor Universal" in response.text

def test_detect_format_video():
    response = client.get("/api/detect-format?filename=video.mp4")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "video"
    assert "mp3" in data["allowed_targets"]
    assert "webm" in data["allowed_targets"]

def test_detect_format_image():
    response = client.get("/api/detect-format?filename=foto.png")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "image"
    assert "webp" in data["allowed_targets"]

def test_detect_format_doc():
    response = client.get("/api/detect-format?filename=contrato.docx")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "document"
    assert "pdf" in data["allowed_targets"]
