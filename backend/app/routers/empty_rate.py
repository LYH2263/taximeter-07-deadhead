from fastapi import APIRouter, HTTPException
from app.repositories.empty_rate import EmptyRateConflict
from app.schemas.fare import EmptyRateActive, EmptyRateCreate, EmptyRateUpdate
from app.services.taxi_service import TaxiService

router = APIRouter()

@router.get("/empty-rates")
def list_empty_rates():
    with TaxiService() as s: return {"items": s.empty_rates()}

@router.post("/empty-rates", status_code=201)
def create_empty_rate(body: EmptyRateCreate):
    with TaxiService() as s:
        try:
            return s.create_empty_rate(body.per_km, body.active)
        except EmptyRateConflict as e:
            raise HTTPException(409, str(e))

@router.put("/empty-rates/{rid}")
def update_empty_rate(rid: int, body: EmptyRateUpdate):
    with TaxiService() as s:
        row = s.update_empty_rate(rid, body.per_km)
        if not row: raise HTTPException(404)
        return row

@router.post("/empty-rates/{rid}/active")
def set_empty_rate_active(rid: int, body: EmptyRateActive):
    with TaxiService() as s:
        try:
            row = s.set_empty_rate_active(rid, body.active)
        except EmptyRateConflict as e:
            raise HTTPException(409, str(e))
        if not row: raise HTTPException(404)
        return row
