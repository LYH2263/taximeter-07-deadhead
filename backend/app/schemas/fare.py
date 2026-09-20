from pydantic import BaseModel, Field

class FareRequest(BaseModel):
    distance_km: float = Field(ge=0)
    slow_min: float = Field(ge=0)
    night: bool = False
    empty_km: float = Field(default=0, ge=0)
    trip_id: int | None = None
    persist: bool = True

class CompareRequest(BaseModel):
    distance_km: float = Field(ge=0)
    slow_min: float = Field(ge=0)
    persist: bool = False

class EmptyRateCreate(BaseModel):
    per_km: float = Field(gt=0)
    active: bool = True

class EmptyRateUpdate(BaseModel):
    per_km: float = Field(gt=0)

class EmptyRateActive(BaseModel):
    active: bool
