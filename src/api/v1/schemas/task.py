from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None


class ReportRequest(BaseModel):
    format: str = "excel"
    email: str | None = None


class ExportFilters(BaseModel):
    is_closed: bool | None = None
    batch_number: int | None = None
    batch_date: str | None = None
    work_center_id: str | None = None
    shift: str | None = None


class ExportRequest(BaseModel):
    format: str = "excel"
    filters: ExportFilters = ExportFilters()

