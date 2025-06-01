# app/modules/customer/models.py

import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.cockroach import Base


class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    caterer_id = Column(String, ForeignKey("caterers.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("caterer_id", "phone", name="uq_customer_caterer_phone"),
    )

    # ── Relationships ───────────────────────────────────────────────────
    # Each Customer belongs to one Caterer
    caterer = relationship("Caterer", back_populates="customers")

    # Each Customer can have multiple Orders
    orders = relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
