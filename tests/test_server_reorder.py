"""Switcher order persists to servers.json; the first server is the default (#84)."""
from __future__ import annotations

from tests.test_file_manager import _seed_server


def _ids(client):
    return [s["id"] for s in client.get("/api/servers").get_json()]


def test_reorder_persists_and_tolerates_stale_ids(client, tmp_servers_root):
    for sid in ("a", "b", "c"):
        _seed_server(tmp_servers_root, sid)

    res = client.put("/api/servers/order", json={"ids": ["c", "a", "b"]})
    assert res.status_code == 200
    assert [s["id"] for s in res.get_json()] == ["c", "a", "b"]
    assert _ids(client) == ["c", "a", "b"]

    # A stale client list: unknown ids are ignored, unlisted servers go last.
    client.put("/api/servers/order", json={"ids": ["b", "gone"]})
    assert _ids(client) == ["b", "c", "a"]


def test_reorder_rejects_bad_body(client, tmp_servers_root):
    _seed_server(tmp_servers_root, "a")
    assert client.put("/api/servers/order", json={"ids": "a"}).status_code == 400
    assert client.put("/api/servers/order", json={"ids": [1]}).status_code == 400
