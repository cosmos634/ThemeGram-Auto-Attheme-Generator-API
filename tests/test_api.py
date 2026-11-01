from io import BytesIO
import base64
import re

from fastapi.testclient import TestClient
from PIL import Image

from app.config import settings
from app.main import create_app

client = TestClient(create_app(validate_config=False))


def png_bytes() -> bytes:
    image = Image.new("RGB", (32, 32), (90, 120, 180))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_api_key_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "a" * 40)
    response = client.post("/api/v1/generate", headers={"X-API-Key": "wrong"}, files={"image": ("x.png", png_bytes(), "image/png")})
    assert response.status_code == 401


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "a" * 40)
    response = client.post("/api/v1/generate", files={"image": ("x.png", png_bytes(), "image/png")})
    assert response.status_code == 401


def test_generate_returns_attheme_with_embedded_wallpaper(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "api_key", "a" * 40)
    template = tmp_path / "base.attheme"
    template.write_text("windowBackgroundWhite=-1\\nactionBarDefault=-2\\n", encoding="utf-8")
    mapping = tmp_path / "mapping.json"
    mapping.write_text('{"windowBackgroundWhite":"background","actionBarDefault":"primary"}', encoding="utf-8")
    monkeypatch.setattr(settings, "template_path", template)
    monkeypatch.setattr(settings, "mapping_path", mapping)
    response = client.post("/api/v1/generate", headers={"X-API-Key": "a" * 40}, files={"image": ("x.png", png_bytes(), "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "generated_theme.attheme" in response.headers["content-disposition"]
    assert b"windowBackgroundWhite=" in response.content
    text = response.content.decode("utf-8")
    match = re.search(r"\nWPS\n([A-Za-z0-9+/=]+)\nWPE\n?$", text)
    assert match
    wallpaper_bytes = base64.b64decode(match.group(1), validate=True)
    wallpaper = Image.open(BytesIO(wallpaper_bytes))
    assert wallpaper.format == "JPEG"
    assert wallpaper.size == (32, 32)
    assert "chat_wallpaper=" not in text


def test_non_image_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "a" * 40)
    response = client.post("/api/v1/generate", headers={"X-API-Key": "a" * 40}, files={"image": ("x.png", b"not an image", "image/png")})
    assert response.status_code == 400


def test_unconfigured_api_key_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    response = client.post("/api/v1/generate", files={"image": ("x.png", png_bytes(), "image/png")})
    assert response.status_code == 503
