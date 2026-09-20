from fastapi import APIRouter
from app.routers import dashboard, dead_fee, fare, history, settings, tariff, trips

api = APIRouter(prefix="/api")
for r in (dashboard, trips, tariff, fare, dead_fee, history, settings):
    api.include_router(r.router)
