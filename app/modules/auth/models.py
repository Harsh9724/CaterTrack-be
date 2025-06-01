# app/modules/auth/models.py
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey,Boolean
from sqlalchemy.sql import func
from app.db.cockroach import Base

class User(Base):
    __tablename__ = "users"
    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    caterer_id      = Column(String, ForeignKey("caterers.id"), nullable=False)
    email           = Column(String, unique=True, index=True, nullable=False)
    contact         = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role            = Column(Enum("OWNER","MANAGER","CASHIER", name="user_roles"), nullable=False, default="CASHIER")
    created_at      = Column(DateTime, server_default=func.now())

class Invite(Base):
    __tablename__ = "invites"
    token       = Column(String, primary_key=True)   # a UUID4
    caterer_id  = Column(String, ForeignKey("caterers.id"), nullable=False)
    email       = Column(String, nullable=False)
    role        = Column(Enum("MANAGER","CASHIER", name="invite_roles"), nullable=False)
    created_at  = Column(DateTime, server_default=func.now())
    used        = Column(Boolean, default=False)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    token      = Column(String, primary_key=True, index=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used       = Column(Boolean, default=False, nullable=False)