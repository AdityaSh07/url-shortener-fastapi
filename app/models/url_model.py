from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text

from ..database.database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    original_url = Column(
        Text,
        nullable=False
    )

    short_code = Column(
        String(10),
        nullable=False,
        unique=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )