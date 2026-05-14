from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from axiom_api.models.base import Base


class OidcSession(Base):
    __tablename__ = "sessions"

    sid: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_sub: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Cached identity claims (groups + roles) refreshed on token refresh
    claims: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    id_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    access_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    refresh_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
