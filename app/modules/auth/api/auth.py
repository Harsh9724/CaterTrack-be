from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import (
    APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
)
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.dependencies.database import get_sql_db
from app.modules.auth import models, schemas
from app.modules.caterer.models import Caterer
from app.utils.email import EmailService
from app.modules.auth.api.deps import get_current_owner

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
mailer  = EmailService()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@router.post("/register", response_model=schemas.UserOut)
def register_tenant(
    payload: schemas.UserCreate,
    db: Session = Depends(get_sql_db),
):
    # 1) create Caterer
    cat = Caterer(name=payload.contact, email=payload.email, contact=payload.contact)
    db.add(cat); db.commit(); db.refresh(cat)

    # 2) create OWNER user
    hashed = pwd_ctx.hash(payload.password)
    user = models.User(
        caterer_id      = cat.id,
        email           = payload.email,
        contact         = payload.contact,
        hashed_password = hashed,
        role            = "OWNER",
    )
    db.add(user); db.commit(); db.refresh(user)

    # 3) return user info
    return schemas.UserOut(id=user.id, email=user.email, contact=user.contact)


@router.post("/login", response_model=schemas.Token)
def login(
    payload: schemas.UserLogin,
    db: Session = Depends(get_sql_db),
):
    user = db.query(models.User).filter_by(email=payload.email).first()
    if not user or not pwd_ctx.verify(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token({
        "sub": user.id,
        "tid": user.caterer_id,
        "role": user.role,
    })
    return schemas.Token(access_token=token)



@router.post("/invite", response_model=str)
def invite_staff(
    payload: schemas.InviteCreate,
    background: BackgroundTasks,
    current_user: models.User = Depends(get_current_owner),  # <— fixed here
    db: Session = Depends(get_sql_db),
):
    token = str(uuid4())
    inv = models.Invite(
        token      = token,
        caterer_id = current_user.caterer_id,
        email      = payload.email,
        role       = payload.role,
    )
    db.add(inv); db.commit()

    accept_url = f"{settings.frontend_url}/auth/accept?token={token}"
    html = f"""
      <p>You’ve been invited as <strong>{payload.role}</strong> to CaterTrack.</p>
      <p><a href="{accept_url}">Click here to accept your invitation</a></p>
    """
    background.add_task(
        mailer.send_email,
        payload.email,
        "You’re invited to CaterTrack",
        html
    )
    return token

@router.post("/accept", response_model=schemas.Token)
async def accept_invite(
    request: Request,
    payload: schemas.InviteAccept,
    db: Session = Depends(get_sql_db),
):
    raw = await request.body()
    print("── RAW BODY ──", raw)
      
    inv = db.query(models.Invite).filter_by(token=payload.token, used=False).first()
    if not inv:
        raise HTTPException(404, "Invalid or expired invite")
    hashed = pwd_ctx.hash(payload.password)
    user = models.User(
        caterer_id      = inv.caterer_id,
        email           = inv.email,
        contact         = payload.contact or "",
        hashed_password = hashed,
        role            = inv.role,
    )
    db.add(user)
    inv.used = True
    db.commit()
    token = create_access_token({
        "sub": user.id,
        "tid": user.caterer_id,
        "role": user.role,
    })
    return schemas.Token(access_token=token)


@router.post("/forgot-password", response_model=str)
def forgot_password(
    payload: schemas.ForgotPassword,
    background: BackgroundTasks,
    db: Session = Depends(get_sql_db),
):
    user = db.query(models.User).filter_by(email=payload.email).first()
    if not user:
        # don't reveal whether email exists
        return "If that email is registered, you’ll get a reset link shortly"

    token = str(uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    pr = models.PasswordReset(token=token, user_id=user.id, expires_at=expires)
    db.add(pr); db.commit()

    reset_url = f"{settings.frontend_url}/auth/reset-password?token={token}"
    html = f"""
      <p>Reset your password by clicking the link below (valid for 1 hour):</p>
      <p><a href="{reset_url}">Reset Password</a></p>
    """
    background.add_task(mailer.send_email, payload.email, "Reset your CaterTrack password", html)
    return "If that email is registered, you’ll get a reset link shortly"


@router.post("/reset-password", response_model=schemas.Token)
def reset_password(
    payload: schemas.ResetPassword,
    db: Session = Depends(get_sql_db),
):
    pr = db.query(models.PasswordReset).filter_by(token=payload.token, used=False).first()
    if not pr or pr.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invalid or expired reset token")
    user = db.query(models.User).get(pr.user_id)
    user.hashed_password = pwd_ctx.hash(payload.password)
    pr.used = True
    db.commit()

    token = create_access_token({
        "sub": user.id,
        "tid": user.caterer_id,
        "role": user.role,
    })
    return schemas.Token(access_token=token)
