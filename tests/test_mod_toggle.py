"""Enable/disable mods by renaming to ``.jar.disabled`` (#83)."""
from __future__ import annotations

from backend.server import storage
from tests.test_file_manager import _seed_server


def test_toggle_renames_jar_and_moves_manifest(client, tmp_servers_root):
    mods = _seed_server(tmp_servers_root) / "mods"
    mods.mkdir()
    (mods / "sodium.jar").write_bytes(b"a")
    (mods / "lithium.jar").write_bytes(b"b")
    (mods / "lithium.jar.disabled").write_bytes(b"old")
    storage.record_content_install("srv1", "sodium.jar", {"projectId": "AANobbMI"})

    res = client.patch("/api/servers/srv1/mods", json={
        "filenames": ["sodium.jar", "lithium.jar", "../escape.jar", "missing.jar"],
        "enabled": False,
    })
    body = res.get_json()
    assert res.status_code == 200
    assert body["renamed"] == {"sodium.jar": "sodium.jar.disabled"}
    # lithium collides with an existing disabled copy; the other two are rejected.
    assert {e["filename"] for e in body["errors"]} == {"lithium.jar", "../escape.jar", "missing.jar"}
    assert (mods / "sodium.jar.disabled").is_file() and not (mods / "sodium.jar").exists()
    assert storage.get_content_manifest("srv1") == {"sodium.jar.disabled": {"projectId": "AANobbMI"}}

    # Listing still shows it; enabling it puts everything back.
    names = [e["name"] for e in client.get("/api/servers/srv1/mods").get_json()]
    assert "sodium.jar.disabled" in names
    res = client.patch("/api/servers/srv1/mods", json={"filenames": ["sodium.jar.disabled"], "enabled": True})
    assert res.get_json()["renamed"] == {"sodium.jar.disabled": "sodium.jar"}
    assert storage.get_content_manifest("srv1") == {"sodium.jar": {"projectId": "AANobbMI"}}

    # Already-enabled jars are a no-op, not an error.
    res = client.patch("/api/servers/srv1/mods", json={"filenames": ["sodium.jar"], "enabled": True})
    assert res.get_json() == {"success": True, "renamed": {}, "errors": []}


def test_toggle_validates_body(client, tmp_servers_root):
    _seed_server(tmp_servers_root)
    assert client.patch("/api/servers/srv1/mods", json={"filenames": [], "enabled": True}).status_code == 400
    assert client.patch("/api/servers/srv1/mods", json={"filenames": ["a.jar"]}).status_code == 400
