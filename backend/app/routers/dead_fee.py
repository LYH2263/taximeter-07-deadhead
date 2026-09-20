from fastapi import APIRouter, HTTPException
from app.repositories.dead_fee import (
    DeadRateCodeExists,
    DeadRateConflict,
    DeadRateNotFound,
)
from app.schemas.dead_fee import DeadRateCreate, DeadRateUpdate
from app.services.taxi_service import TaxiService

router = APIRouter()


@router.get("/dead-km-rates")
def list_dead_rates():
    with TaxiService() as s:
        return {"items": s.list_dead_rates()}


@router.post("/dead-km-rates", status_code=201)
def create_dead_rate(body: DeadRateCreate):
    with TaxiService() as s:
        try:
            return s.create_dead_rate(body.code.strip(), body.name, body.price_per_km, body.active)
        except DeadRateConflict as e:
            raise HTTPException(status_code=409, detail=str(e))
        except DeadRateCodeExists as e:
            raise HTTPException(status_code=409, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))


@router.patch("/dead-km-rates/{rate_id}")
def update_dead_rate(rate_id: int, body: DeadRateUpdate):
    with TaxiService() as s:
        try:
            return s.update_dead_rate(rate_id, body.name, body.price_per_km, body.active)
        except DeadRateConflict as e:
            raise HTTPException(status_code=409, detail=str(e))
        except DeadRateNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
