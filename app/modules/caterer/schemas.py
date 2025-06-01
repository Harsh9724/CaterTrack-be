# app/modules/caterer/schemas.py

from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict
from typing import Optional
from datetime import datetime

class CatererBase(BaseModel):
    name: str
    email: EmailStr
    contact: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    description: Optional[str] = None
    profile_image_url: Optional[HttpUrl] = None

    # Allow reading from ORM objects
    model_config = ConfigDict(from_attributes=True)

class CatererCreate(CatererBase):
    pass

class CatererUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    description: Optional[str] = None
    profile_image_url: Optional[HttpUrl] = None

    # Used only for input, no ORM output needed here
    model_config = ConfigDict(from_attributes=True)

class CatererOut(CatererBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
