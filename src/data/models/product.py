from datetime import datetime

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    unique_code: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), nullable=False, index=True
    )

    is_aggregated: Mapped[bool] = mapped_column(default=False, index=True)
    aggregated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    batch: Mapped["Batch"] = relationship(back_populates="products")  # noqa: F821 — forward ref, класс в другом модуле

    __table_args__ = (
        Index("idx_product_batch_aggregated", "batch_id", "is_aggregated"),
    )
