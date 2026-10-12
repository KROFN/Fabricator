"""Upload any image as the server's 64x64 server-icon.png (#85)."""
from __future__ import annotations

import io

from PIL import Image

from tests.test_file_manager import _seed_server


def _jpeg(size):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, "JPEG")
    return buf.getvalue()


def test_icon_is_resized_served_and_removed(client, tmp_servers_root):
    install = _seed_server(tmp_servers_root)
    assert client.get("/api/servers/srv1/icon").status_code == 404

    res = client.put("/api/servers/srv1/icon", data=_jpeg((300, 200)), content_type="image/jpeg")
    assert res.status_code == 200
    with Image.open(install / "server-icon.png") as icon:
        assert (icon.format, icon.size) == ("PNG", (64, 64))

    res = client.get("/api/servers/srv1/icon")
    assert res.status_code == 200 and res.mimetype == "image/png"
    res.close()

    assert client.delete("/api/servers/srv1/icon").status_code == 200
    assert not (install / "server-icon.png").exists()


def test_icon_rejects_non_images_and_huge_dimensions(client, tmp_servers_root):
    install = _seed_server(tmp_servers_root)
    assert client.put("/api/servers/srv1/icon", data=b"not an image").status_code == 400
    buf = io.BytesIO()
    Image.new("1", (5000, 5000)).save(buf, "PNG")  # tiny file, 25M pixels
    assert client.put("/api/servers/srv1/icon", data=buf.getvalue()).status_code == 400
    assert not (install / "server-icon.png").exists()
