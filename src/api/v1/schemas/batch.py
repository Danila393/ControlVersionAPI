from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.api.v1.schemas.product import ProductRead


class BatchCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    is_closed: bool = Field(default=False, alias="СтатусЗакрытия")
    task_description: str = Field(alias="ПредставлениеЗаданияНаСмену")
    work_center_identifier: str = Field(alias="ИдентификаторРЦ")
    work_center_name: str = Field(alias="РабочийЦентр")
    shift: str = Field(alias="Смена")
    team: str = Field(alias="Бригада")
    batch_number: int = Field(alias="НомерПартии")
    batch_date: date = Field(alias="ДатаПартии")
    nomenclature: str = Field(alias="Номенклатура")
    ekn_code: str = Field(alias="КодЕКН")
    shift_start: datetime = Field(alias="ДатаВремяНачалаСмены")
    shift_end: datetime = Field(alias="ДатаВремяОкончанияСмены")


class BatchUpdate(BaseModel):
    is_closed: bool | None = None
    task_description: str | None = None
    shift: str | None = None
    team: str | None = None
    nomenclature: str | None = None
    ekn_code: str | None = None
    shift_start: datetime | None = None
    shift_end: datetime | None = None


class BatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_closed: bool
    batch_number: int
    batch_date: date
    products: list[ProductRead] = []