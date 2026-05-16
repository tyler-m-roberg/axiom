import enum
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom_api.models.base import Base, PgEnum, TimestampedMixin


class AclPermission(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class TestAcl(Base, TimestampedMixin):
    __tablename__ = "test_acls"
    __table_args__ = (
        UniqueConstraint("test_id", "group_id", name="uq_test_acl_test_group"),
    )

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    permission: Mapped[AclPermission] = mapped_column(
        PgEnum(AclPermission, name="acl_permission"), nullable=False, default=AclPermission.WRITE
    )

    test = relationship("Test", back_populates="acls")
