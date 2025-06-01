from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email:   EmailStr
    contact: str
    password: str

class UserLogin(BaseModel):
    email:   EmailStr
    password: str

class UserOut(BaseModel):
    id:      str
    email:   EmailStr
    contact: str

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class InviteCreate(BaseModel):
    email: EmailStr
    role:  str       # MANAGER or CASHIER

class InviteAccept(BaseModel):
    token:   str
    password: str
    contact: Optional[str]

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token:    str
    password: str
