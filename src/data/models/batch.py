from datetime import date, datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)

    is_closed: Mapped[bool] = mapped_column(default=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    task_description: Mapped[str] = mapped_column(nullable=False)
    work_center_id: Mapped[int] = mapped_column(ForeignKey("work_centers.id"), nullable=False)
    shift: Mapped[str] = mapped_column(nullable=False)
    team: Mapped[str] = mapped_column(nullable=False)

    batch_number: Mapped[int] = mapped_column(nullable=False, index=True)
    batch_date: Mapped[date] = mapped_column(nullable=False, index=True)

    nomenclature: Mapped[str] = mapped_column(nullable=False)
    ekn_code: Mapped[str] = mapped_column(nullable=False)

    shift_start: Mapped[datetime] = mapped_column(nullable=False)
    shift_end: Mapped[datetime] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    work_center: Mapped["WorkCenter"] = relationship()  # noqa: F821 — forward ref, класс в другом модуле
    products: Mapped[list["Product"]] = relationship(back_populates="batch")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("batch_number", "batch_date", name="uq_batch_number_date"),
        Index("idx_batch_closed", "is_closed"),
        Index("idx_batch_shift_times", "shift_start", "shift_end"),
    )


