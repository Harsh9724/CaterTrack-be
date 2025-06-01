# app/modules/caterer/api/profile.py

import os
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Request,
)
from sqlalchemy.orm import Session

from app.modules.caterer import models, schemas
from app.modules.auth.api.deps import get_current_user
from app.dependencies.database import get_sql_db

router = APIRouter(
    prefix="/caterer/profile",
    tags=["caterer"],
)


@router.get("", response_model=schemas.CatererOut)
def view_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_sql_db),
):
    caterer = db.query(models.Caterer).filter_by(id=current_user.caterer_id).first()
    if not caterer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    return caterer


@router.put("", response_model=schemas.CatererOut)
async def update_profile(
    request: Request,
    name: Optional[str] = Form(None),
    contact: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_sql_db),
):
    caterer = db.query(models.Caterer).filter_by(id=current_user.caterer_id).first()
    if not caterer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    # ─── 1) Handle file upload ──────────────────────────────────────────────
    if profile_image:
        # Save under "<project_root>/static/profile_images"
        # If you used Option 1, that folder already exists.
        # If you used Option 2, STATIC_DIR was created at startup.
        upload_folder = os.path.join(os.getcwd(), "static", "profile_images")
        os.makedirs(upload_folder, exist_ok=True)

        original_name = profile_image.filename
        ext = os.path.splitext(original_name)[1]
        unique_name = f"{caterer.id}_{uuid.uuid4().hex}{ext}"
        file_location = os.path.join(upload_folder, unique_name)

        with open(file_location, "wb") as f:
            contents = await profile_image.read()
            f.write(contents)

        base_url = str(request.base_url).rstrip("/")  # e.g. "http://localhost:8000"
        image_url = f"{base_url}/static/profile_images/{unique_name}"
        caterer.profile_image_url = image_url

    # ─── 2) Update any other text fields ────────────────────────────────────
    if name is not None:
        caterer.name = name.strip()
    if contact is not None:
        caterer.contact = contact.strip()
    if address is not None:
        caterer.address = address.strip() or None
    if city is not None:
        caterer.city = city.strip() or None
    if state is not None:
        caterer.state = state.strip() or None
    if postal_code is not None:
        caterer.postal_code = postal_code.strip() or None
    if description is not None:
        caterer.description = description.strip() or None

    db.commit()
    db.refresh(caterer)
    return caterer
