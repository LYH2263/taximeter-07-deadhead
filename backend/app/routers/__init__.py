from fastapi import APIRouter
from app.routers import dashboard, empty_rate, fare, history, settings, tariff, trips

api = APIRouter(prefix="/api")
for r in (dashboard, trips, tariff, fare, history, settings, empty_rate):
    api.include_router(r.router)
