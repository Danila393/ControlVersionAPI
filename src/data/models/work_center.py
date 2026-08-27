from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func

from datetime import datetime

from src.core.database import Base


class WorkCenter(Base):
    __tablename__ = "work_centers"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(unique=True, nullable=False, index=True) # ИдентификаторРЦ
    name: Mapped[str] = mapped_column(nullable=False) # Название рабочего центра
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())