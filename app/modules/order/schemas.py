# app/modules/order/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict

#
# ─── 1.1  Event Schemas ──────────────────────────────────────────────────────
#
class EventIn(BaseModel):
    event_type:     str
    event_date:     datetime
    start_time:     str
    end_time:       str
    venue:          str
    no_of_guests:   int
    extra_services: Optional[Dict] = None
    menu:           Optional[Dict] = None
    total_amount:   float


class EventUpdate(BaseModel):
    event_type:     Optional[str]    = None
    event_date:     Optional[datetime] = None
    start_time:     Optional[str]    = None
    end_time:       Optional[str]    = None
    venue:          Optional[str]    = None
    no_of_guests:   Optional[int]    = None
    extra_services: Optional[Dict]   = None
    menu:           Optional[Dict]   = None
    total_amount:   Optional[float]  = None


class EventOut(EventIn):
    event_id:      str
    created_at:    datetime
    updated_at:    Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


#
# ─── 1.2  Order Schemas ──────────────────────────────────────────────────────
#
class OrderIn(BaseModel):
    customer_id: str
    events:      List[EventIn]


class OrderWithCustomerIn(BaseModel):
    phone: str
    name: Optional[str]
    email: Optional[str]
    events: List[EventIn]


class CustomerOut(BaseModel):
    customer_id: str
    name:        str
    phone:       str
    email:       Optional[str]

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    order_id:    str
    customer:    CustomerOut
    events:      List[EventOut]
    grand_total: Decimal
    paid_till_now:     Decimal
    due:         Decimal
    paid_status: str
    created_at:  datetime
    updated_at:  Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ─── Payment Schemas ─────────────────────────────────────────

class PaymentIn(BaseModel):
    amount: Decimal
    datetime: datetime
    type: str
    notes: Optional[str] = None

class PaymentOut(PaymentIn):
    payment_id: str

    model_config = ConfigDict(from_attributes=True)