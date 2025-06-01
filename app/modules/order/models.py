# app/modules/order/models.py

import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.orm import relationship
from app.db.cockroach import Base


class Order(Base):
    __tablename__ = "order"

    order_id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    caterer_id = Column(
        String, ForeignKey("caterers.id"), nullable=False
    )
    customer_id = Column(
        String, ForeignKey("customer.customer_id"), nullable=False
    )
    created_at = Column(
        DateTime, server_default=func.now()
    )
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Payment fields
    grand_total = Column(Numeric(10, 2), default=0)
    advance = Column(Numeric(10, 2), default=0)
    due = Column(Numeric(10, 2), default=0)
    paid_status = Column(String, default="UNPAID")

    # ── Relationships ───────────────────────────────────────────────────
    # Each Order belongs to one Customer
    customer = relationship("Customer", back_populates="orders")

    # Each Order belongs to one Caterer
    caterer = relationship("Caterer", back_populates="orders")
