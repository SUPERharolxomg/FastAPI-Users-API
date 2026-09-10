from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"