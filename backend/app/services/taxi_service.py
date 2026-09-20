from app.db import connect
from app.engines.night_compare import compare_day_night
from app.engines.dead_fee import calc_dead_fee
from app.engines.tariff_breakdown import calc_fare
from app.repositories import dead_fee, runs, settings, tariff, trips

class TaxiService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_trips(self): return trips.list_all(self._c)
    def trip(self, tid): return trips.get(self._c, tid)
    def tariff(self): return tariff.get_active(self._c)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def fare(self, distance_km, slow_min, night, trip_id, persist, dead_km=0.0):
        t = tariff.get_active(self._c)
        # 载客段：现行起步、里程、低速与夜间布尔，拆解逻辑不变
        occupied = calc_fare(distance_km, slow_min, night, t)
        # 空驶段：不加起步、不计低速，仅启用单价 × 空驶公里；无启用单价时为 0
        dead = calc_dead_fee(dead_km, dead_fee.get_active(self._c))
        payable = round(occupied["total"] + dead["dead_fee"], 2)
        r = {
            "distance_km": occupied["distance_km"],
            "slow_min": occupied["slow_min"],
            "night": occupied["night"],
            "night_factor": occupied["night_factor"],
            # 载客三项
            "start": occupied["start"],
            "mileage": occupied["mileage"],
            "slow_fee": occupied["slow_fee"],
            "occupied_total": occupied["total"],
            # 空驶
            "dead_km": dead["dead_km"],
            "dead_rate_id": dead["dead_rate_id"],
            "dead_rate_code": dead["dead_rate_code"],
            "dead_price_per_km": dead["dead_price_per_km"],
            "dead_fee": dead["dead_fee"],
            # 应付 = 载客应付 + 空驶费
            "payable": payable,
            "total": payable,
        }
        payload = {"distance_km": distance_km, "slow_min": slow_min, "dead_km": dead_km, "night": night}
        rid = runs.insert(self._c, "fare", payload, r, trip_id) if persist else None
        return {"run_id": rid, **r}
    def compare(self, distance_km, slow_min, persist):
        t = tariff.get_active(self._c)
        r = compare_day_night(distance_km, slow_min, t)
        rid = runs.insert(self._c, "compare", {"distance_km": distance_km, "slow_min": slow_min}, r, None) if persist else None
        return {"run_id": rid, **r}
    def list_dead_rates(self): return dead_fee.list_all(self._c)
    def create_dead_rate(self, code, name, price_per_km, active):
        return dead_fee.create(self._c, code, name, price_per_km, active)
    def update_dead_rate(self, rate_id, name=None, price_per_km=None, active=None):
        return dead_fee.update(self._c, rate_id, name, price_per_km, active)
    def dashboard(self):
        items = trips.list_all(self._c)
        clean = [x for x in items if "种子" not in x["label"]]
        dirty = [x for x in items if "种子" in x["label"]]
        return {"trip_count": len(items), "clean": len(clean), "dirty": len(dirty)}
