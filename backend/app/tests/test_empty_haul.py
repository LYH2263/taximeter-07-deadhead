import json
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from fastapi.testclient import TestClient
from app import seed
from app.main import app
from app.engines.tariff_breakdown import calc_fare

seed.init_db()  # 不依赖 startup 事件，直接建库
client = TestClient(app)
T = {"start_price": 11, "start_include_km": 3, "per_km": 2.5, "per_slow_min": 0.8, "night_factor": 1.2}


def test_empty_fee_added_to_payable():
    r = client.post("/api/fare", json={"distance_km": 8, "slow_min": 3, "night": False, "empty_km": 4, "persist": True})
    assert r.status_code == 200
    b = r.json()
    loaded = calc_fare(8, 3, False, T)
    assert b["start"] == loaded["start"] and b["mileage"] == loaded["mileage"] and b["slow_fee"] == loaded["slow_fee"]
    assert b["total"] == loaded["total"]
    assert b["empty_km"] == 4.0 and b["empty_per_km"] == 1.5
    assert b["empty_fee"] == 6.0
    assert b["payable"] == round(loaded["total"] + 6.0, 2)


def test_negative_empty_km_rejected_no_record():
    before = len(client.get("/api/history").json()["items"])
    r = client.post("/api/fare", json={"distance_km": 8, "slow_min": 3, "empty_km": -1, "persist": True})
    assert r.status_code == 422
    after = len(client.get("/api/history").json()["items"])
    assert after == before


def test_readonly_trial_writes_nothing():
    before = len(client.get("/api/history").json()["items"])
    r = client.post("/api/fare", json={"distance_km": 8, "slow_min": 3, "empty_km": 4, "persist": False})
    assert r.status_code == 200 and r.json()["run_id"] is None
    after = len(client.get("/api/history").json()["items"])
    assert after == before


def test_disabled_rate_zero_empty_fee():
    rates = client.get("/api/empty-rates").json()["items"]
    active = [x for x in rates if x["active"]][0]
    client.post(f"/api/empty-rates/{active['id']}/active", json={"active": False})
    r = client.post("/api/fare", json={"distance_km": 8, "slow_min": 3, "empty_km": 4, "persist": False})
    b = r.json()
    assert b["empty_fee"] == 0.0 and b["empty_per_km"] is None
    assert b["payable"] == b["total"]
    client.post(f"/api/empty-rates/{active['id']}/active", json={"active": True})


def test_single_active_conflict_names_both():
    r = client.post("/api/empty-rates", json={"per_km": 2.0, "active": True})
    assert r.status_code == 409
    msg = r.json()["detail"]
    assert "#1" in msg and "#" in msg  # 点名已启用 #1 与新单价
    r2 = client.post("/api/empty-rates", json={"per_km": 2.0, "active": False})
    assert r2.status_code == 201
    rid = r2.json()["id"]
    r3 = client.post(f"/api/empty-rates/{rid}/active", json={"active": True})
    assert r3.status_code == 409
    assert f"#{rid}" in r3.json()["detail"] and "#1" in r3.json()["detail"]


def test_rate_must_be_positive():
    assert client.post("/api/empty-rates", json={"per_km": 0, "active": False}).status_code == 422
    assert client.post("/api/empty-rates", json={"per_km": -2, "active": False}).status_code == 422
    rates = client.get("/api/empty-rates").json()["items"]
    rid = rates[-1]["id"]
    assert client.put(f"/api/empty-rates/{rid}", json={"per_km": 0}).status_code == 422


def test_price_change_does_not_rewrite_history():
    r = client.post("/api/fare", json={"distance_km": 8, "slow_min": 3, "empty_km": 4, "persist": True})
    rid = r.json()["run_id"]
    rates = client.get("/api/empty-rates").json()["items"]
    active = [x for x in rates if x["active"]][0]
    client.put(f"/api/empty-rates/{active['id']}", json={"per_km": 9.9})
    items = client.get("/api/history").json()["items"]
    rec = [x for x in items if x["id"] == rid][0]
    snap = json.loads(rec["result_json"])
    assert snap["empty_fee"] == 6.0 and snap["empty_per_km"] == 1.5
    assert json.loads(rec["input_json"])["empty_km"] == 4
    client.put(f"/api/empty-rates/{active['id']}", json={"per_km": 1.5})


def test_trip_detail_default_empty_zero():
    r = client.post("/api/fare", json={"distance_km": 5, "slow_min": 2, "night": False, "trip_id": 1, "persist": False})
    b = r.json()
    assert b["empty_km"] == 0.0 and b["empty_fee"] == 0.0
    assert b["payable"] == b["total"]
