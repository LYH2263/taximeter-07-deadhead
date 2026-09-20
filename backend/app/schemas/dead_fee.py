from pydantic import BaseModel, Field

class DeadRateCreate(BaseModel):
    code: str = Field(min_length=1)
    name: str = ""
    price_per_km: float = Field(gt=0)
    active: bool = False

class DeadRateUpdate(BaseModel):
    name: str | None = None
    price_per_km: float | None = Field(default=None, gt=0)
    active: bool | None = None
