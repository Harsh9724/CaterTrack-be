# app/modules/auth/api/deps.py

from typing import Literal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies.database import get_sql_db
from app.modules.auth import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData:
    sub: str
    tid: str
    role: Literal["OWNER", "MANAGER", "CASHIER"]


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_token_data(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        data = TokenData()
        data.sub = payload.get("sub")
        data.tid = payload.get("tid")
        data.role = payload.get("role")
        if not data.sub or not data.tid or not data.role:
            raise credentials_exception
        return data
    except JWTError:
        raise credentials_exception


def get_current_user(
    token_data: TokenData = Depends(get_current_token_data),
    db: Session = Depends(get_sql_db),
) -> models.User:
    user = db.query(models.User).get(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Optional: check user.caterer_id == token_data.tid
    if user.caterer_id != token_data.tid:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    # If you add `is_active` on User, check it here
    return current_user


def get_current_owner(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if current_user.role != "OWNER":
        raise HTTPException(status_code=403, detail="Requires OWNER role")
    return current_user


def get_current_manager_or_owner(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if current_user.role not in ("OWNER", "MANAGER"):
        raise HTTPException(status_code=403, detail="Requires MANAGER or OWNER role")
    return current_user
