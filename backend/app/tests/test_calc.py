import json

import pytest
from pydantic import ValidationError

from app import seed
from app.db import connect
from app.engines.dead_fee import calc_dead_fee
from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare
from app.main import app
from app.repositories import dead_fee, runs
from app.schemas.fare import FareRequest
from app.services.taxi_service import TaxiService
from fastapi.testclient import TestClient

T = {"start_price": 11, "start_include_km": 3, "per_km": 2.5, "per_slow_min": 0.8, "night_factor": 1.2}


@pytest.fixture(scope="module", autouse=True)
def seeded():
    seed.init_db()
    yield


# ---------- 改造前一致性：载客拆解 ----------

def test_day_short():
    r = calc_fare(5, 2, False, T)
    assert r["total"] == 17.6
    assert r["mileage"] == 5.0

def test_night_long():
    r = calc_fare(18, 12, True, T)
    assert r["total"] == 69.72

def test_compare_delta():
    c = compare_day_night(18, 12, T)
    assert c["night_total"] > c["day_total"]


# ---------- 空驶引擎 ----------

def test_dead_engine_basic():
    rate = {"id": 1, "code": "standard", "price_per_km": 1.5}
    d = calc_dead_fee(10, rate)
    assert d["dead_fee"] == 15.0
    assert d["dead_price_per_km"] == 1.5

def test_dead_engine_no_active_rate_is_zero():
    d = calc_dead_fee(10, None)
    assert d["dead_fee"] == 0.0
    assert d["dead_rate_id"] is None


# ---------- 打表服务：载客三项 / 空驶费 / 应付 ----------

def test_fare_split_and_payable():
    with TaxiService() as s:
        r = s.fare(5, 2, False, None, False, dead_km=4)
    # 载客三项与改造前同一组输入一致
    assert r["start"] == 11.0
    assert r["mileage"] == 5.0
    assert r["slow_fee"] == 1.6
    assert r["occupied_total"] == 17.6
    # 空驶费 = 种子单价 1.5 × 4
    assert r["dead_km"] == 4.0
    assert r["dead_fee"] == 6.0
    # 应付 = 载客应付 + 空驶费
    assert r["payable"] == 23.6
    assert r["total"] == 23.6
    # 只读试算不写 calc_runs
    assert r["run_id"] is None

def test_dead_default_zero():
    with TaxiService() as s:
        r = s.fare(5, 2, False, None, False)
    assert r["dead_km"] == 0
    assert r["dead_fee"] == 0
    assert r["payable"] == r["occupied_total"]

def test_night_does_not_affect_dead_fee():
    with TaxiService() as s:
        day = s.fare(5, 2, False, None, False, dead_km=4)
        night = s.fare(5, 2, True, None, False, dead_km=4)
    # 夜间只影响载客段，空驶费不乘夜间系数
    assert night["dead_fee"] == day["dead_fee"] == 6.0
    assert night["occupied_total"] > day["occupied_total"]


# ---------- 负数拒绝且不写记录 ----------

def test_negative_dead_km_rejected_by_schema():
    with pytest.raises(ValidationError):
        FareRequest(distance_km=5, slow_min=2, dead_km=-3, persist=True)

def test_negative_dead_km_writes_no_record():
    before = len(runs.list_recent(connect(), 1000))
    with pytest.raises(ValidationError):
        FareRequest(distance_km=5, slow_min=2, dead_km=-1, persist=True)
    after = len(runs.list_recent(connect(), 1000))
    assert before == after


# ---------- 单价必须为正 ----------

def test_rate_price_must_be_positive():
    from app.schemas.dead_fee import DeadRateCreate
    with pytest.raises(ValidationError):
        DeadRateCreate(code="zero", price_per_km=0)
    with pytest.raises(ValidationError):
        DeadRateCreate(code="neg", price_per_km=-2)
    with TaxiService() as s:
        with pytest.raises(ValueError):
            s.create_dead_rate("zero", "零价", 0, False)


# ---------- 只允许一条启用，冲突点名两条标识 ----------

def test_only_one_active_conflict_names_both():
    with TaxiService() as s:
        # 种子已有一条启用的 standard
        with pytest.raises(dead_fee.DeadRateConflict) as ei:
            s.create_dead_rate("extra", "另一档", 2.0, True)
        msg = str(ei.value)
        assert "standard" in msg
        assert "extra" in msg
        # 停用态可以新增多条
        created = s.create_dead_rate("inactive_x", "停用档", 2.2, False)
        assert created["active"] == 0
        # 已有启用时，把停用档改成启用同样被点名
        with pytest.raises(dead_fee.DeadRateConflict) as ei2:
            s.update_dead_rate(created["id"], active=True)
        msg2 = str(ei2.value)
        assert "standard" in msg2 and "inactive_x" in msg2


# ---------- 停用后空驶费为零 ----------

def test_disabled_rate_dead_fee_zero():
    with TaxiService() as s:
        active = next(x for x in s.list_dead_rates() if x["code"] == "standard")
        s.update_dead_rate(active["id"], active=False)
        try:
            r = s.fare(5, 2, False, None, False, dead_km=8)
            assert r["dead_fee"] == 0
            assert r["payable"] == r["occupied_total"] == 17.6
        finally:
            s.update_dead_rate(active["id"], active=True)


# ---------- 已写入记录保留当时空驶公里与空驶费，后来改单价不改写 ----------

def test_history_snapshot_survives_price_change():
    conn = connect()
    with TaxiService() as s:
        active = next(x for x in s.list_dead_rates() if x["code"] == "standard")
        rid = s.fare(5, 2, False, None, True, dead_km=4)["run_id"]
        # 事后把单价从 1.5 改成 9.0
        s.update_dead_rate(active["id"], price_per_km=9.0)
        try:
            row = conn.execute("SELECT * FROM calc_runs WHERE id=?", (rid,)).fetchone()
            payload = json.loads(row["input_json"])
            result = json.loads(row["result_json"])
            assert payload["dead_km"] == 4
            assert result["dead_km"] == 4
            assert result["dead_fee"] == 6.0          # 仍是当时的 1.5×4
            assert result["payable"] == 23.6
            # 新试算按新单价
            fresh = s.fare(5, 2, False, None, False, dead_km=4)
            assert fresh["dead_fee"] == 36.0
        finally:
            s.update_dead_rate(active["id"], price_per_km=1.5)


# ---------- HTTP 层：422 不写库 / 409 冲突点名 / 只读不写 ----------

def test_http_negative_dead_km_422_and_no_write():
    conn = connect()
    with TestClient(app) as client:
        before = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
        r = client.post("/api/fare", json={"distance_km": 5, "slow_min": 2, "dead_km": -3, "persist": True})
        after = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    assert r.status_code == 422
    assert before == after

def test_http_preview_does_not_write():
    conn = connect()
    with TestClient(app) as client:
        before = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
        r = client.post("/api/fare", json={"distance_km": 5, "slow_min": 2, "dead_km": 4, "persist": False})
        after = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    assert r.status_code == 200
    assert before == after
    body = r.json()
    assert body["run_id"] is None
    assert body["dead_fee"] == 6.0
    assert body["payable"] == 23.6

def test_http_rate_conflict_409_names_both():
    with TestClient(app) as client:
        r = client.post("/api/dead-km-rates", json={"code": "http_extra", "name": "冲突档", "price_per_km": 2.0, "active": True})
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "standard" in detail and "http_extra" in detail

def test_http_rate_non_positive_422():
    with TestClient(app) as client:
        r = client.post("/api/dead-km-rates", json={"code": "http_zero", "price_per_km": 0})
    assert r.status_code == 422
