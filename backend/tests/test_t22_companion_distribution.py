from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_install_html_page_rendering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/install")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        html = res.text
        assert "Sonos Network Companion" in html
        assert "/api/companion/apk" in html
        assert "Firewalla" in html or "WireGuard" in html


@pytest.mark.asyncio
async def test_companion_qr_svg_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/companion/qr")
        assert res.status_code == 200
        assert "image/svg+xml" in res.headers["content-type"]
        assert "<svg" in res.text
        assert "</svg>" in res.text


@pytest.mark.asyncio
async def test_companion_apk_download():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/companion/apk")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/vnd.android.package-archive"
        assert "attachment" in res.headers.get("content-disposition", "")
        assert "sonos-network-companion.apk" in res.headers.get("content-disposition", "")
        assert len(res.content) > 0


@pytest.mark.asyncio
async def test_companion_apk_serves_static_file_when_present(tmp_path, monkeypatch):
    static_dir = tmp_path / "backend" / "app" / "static" / "apk"
    static_dir.mkdir(parents=True)
    real_apk = static_dir / "sonos-network-companion.apk"
    real_apk.write_bytes(b"PK\x03\x04RealProductionApkBytes")

    monkeypatch.chdir(tmp_path)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/companion/apk")
        assert res.status_code == 200
        assert res.content == b"PK\x03\x04RealProductionApkBytes"
