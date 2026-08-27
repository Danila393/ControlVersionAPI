from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WebhookCreate(BaseModel):
    url: str
    events: list[str]
    secret_key: str
    retry_count: int = 3
    timeout: int = 10


class WebhookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime


class WebhookListResponse(BaseModel):
    items: list[WebhookRead]
    total: int


class WebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    status: str
    attempts: int
    response_status: int | None
    error_message: str | None
    created_at: datetime
    delivered_at: datetime | None


class WebhookDeliveryListResponse(BaseModel):
    items: list[WebhookDeliveryRead]
    total: int


class WebhookUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    secret_key: str | None = None
    is_active: bool | None = None
    retry_count: int | None = None
    timeout: int | None = None