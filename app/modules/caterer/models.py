# app/modules/caterer/models.py
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.cockroach import Base

from sqlalchemy.orm import relationship
class Caterer(Base):
    __tablename__ = "caterers"

    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    contact = Column(String, nullable=False)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ── Relationships ───────────────────────────────────────────────────
    # A Caterer can have many Customers
    customers = relationship(
        "Customer", back_populates="caterer", cascade="all, delete-orphan"
    )
    # A Caterer can have many Orders directly
    orders = relationship(
        "Order", back_populates="caterer", cascade="all, delete-orphan"
    )
