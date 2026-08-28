from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None


class ReportRequest(BaseModel):
    format: str = "excel"
    email: str | None = None

