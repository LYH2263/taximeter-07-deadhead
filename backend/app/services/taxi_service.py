from app.db import connect
from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare
from app.modules.empty_haul import calc_empty_fee
from app.repositories import empty_rate, runs, settings, tariff, trips

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
    def empty_rates(self): return empty_rate.list_all(self._c)
    def create_empty_rate(self, per_km, active): return empty_rate.create(self._c, per_km, active)
    def update_empty_rate(self, rid, per_km): return empty_rate.update(self._c, rid, per_km)
    def set_empty_rate_active(self, rid, active): return empty_rate.set_active(self._c, rid, active)
    def fare(self, distance_km, slow_min, night, trip_id, persist, empty_km=0.0):
        t = tariff.get_active(self._c)
        r = calc_fare(distance_km, slow_min, night, t)
        rate = empty_rate.get_active(self._c)
        e = calc_empty_fee(empty_km, rate["per_km"] if rate else None)
        r = {**r, **e, "payable": round(r["total"] + e["empty_fee"], 2)}
        payload = {"distance_km": distance_km, "slow_min": slow_min, "night": night, "empty_km": empty_km}
        rid = runs.insert(self._c, "fare", payload, r, trip_id) if persist else None
        return {"run_id": rid, **r}
    def compare(self, distance_km, slow_min, persist):
        t = tariff.get_active(self._c)
        r = compare_day_night(distance_km, slow_min, t)
        rid = runs.insert(self._c, "compare", {"distance_km": distance_km, "slow_min": slow_min}, r, None) if persist else None
        return {"run_id": rid, **r}
    def dashboard(self):
        items = trips.list_all(self._c)
        clean = [x for x in items if "种子" not in x["label"]]
        dirty = [x for x in items if "种子" in x["label"]]
        return {"trip_count": len(items), "clean": len(clean), "dirty": len(dirty)}
