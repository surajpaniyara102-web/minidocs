import os

os.environ["DB_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from main import app

c = TestClient(app)
A = {"X-Username": "alice"}
B = {"X-Username": "bob"}
C = {"X-Username": "carol"}


def test_share_flow():
    d = c.post("/api/docs", json={"title": "Plan"}, headers=A).json()
    assert c.get(f"/api/docs/{d['id']}", headers=B).status_code == 403
    assert c.post(f"/api/docs/{d['id']}/share", json={"username": "bob"}, headers=A).status_code == 200
    assert c.get(f"/api/docs/{d['id']}", headers=B).status_code == 200
    assert c.post(f"/api/docs/{d['id']}/share", json={"username": "carol"}, headers=B).status_code == 403
    assert c.get(f"/api/docs/{d['id']}", headers=C).status_code == 403
    shared_ids = [x["id"] for x in c.get("/api/docs", headers=B).json()["shared"]]
    assert d["id"] in shared_ids


def test_upload_rejects_bad_type():
    r = c.post("/api/upload", files={"file": ("a.exe", b"x")}, headers=A)
    assert r.status_code == 400