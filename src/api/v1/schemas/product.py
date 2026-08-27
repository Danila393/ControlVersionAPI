from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    batch_id: int
    unique_code: str


class ProductAggregateRequest(BaseModel):
    unique_code: str


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unique_code: str
    is_aggregated: bool
    aggregated_at: datetime | None


class AggregateAsyncRequest(BaseModel):
    unique_codes: list[str]