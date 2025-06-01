# app/modules/customer/schemas.py

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class CustomerCreate(BaseModel):
    name:  str
    phone: str
    email: Optional[EmailStr] = None


class CustomerUpdate(BaseModel):
    name: Optional[str]        = None
    phone: Optional[str]       = None
    email: Optional[EmailStr]  = None



class CustomerOut(BaseModel):
    customer_id: str
    name:        str
    phone:       str
    email:       Optional[EmailStr] = None
    created_at:  datetime
    updated_at:  Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)