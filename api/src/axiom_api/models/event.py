import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom_api.models.base import Base, TimestampedMixin


class Event(Base, TimestampedMixin):
    __tablename__ = "events"

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Stored as { "<field_id>": <value>, ... }
    metadata_values: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    # Marker listing field ids that were created on-the-fly via this event
    on_the_fly_field_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )

    test = relationship("Test", back_populates="events")
