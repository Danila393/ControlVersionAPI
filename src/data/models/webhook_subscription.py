from datetime import datetime

from sqlalchemy import ARRAY, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    url: Mapped[str] = mapped_column(nullable=False)

    events: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    secret_key: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    retry_count: Mapped[int] = mapped_column(default=3)
    timeout: Mapped[int] = mapped_column(default=10)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    deliveries: Mapped[list["WebhookDelivery"]] = relationship(  # noqa: F821 — forward ref, класс в другом модуле
        back_populates="subscription"
    )
