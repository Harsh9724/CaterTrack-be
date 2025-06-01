# app/modules/customer/api/customer.py

from typing import List, Optional, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.modules.customer import models, schemas
from app.dependencies.database import get_sql_db
from app.modules.auth.api.deps import get_current_active_user

router = APIRouter(
    prefix="/caterer/{cid}/customer",
    tags=["customer"],
)

def check_tenant(cid: str, current_user=Depends(get_current_active_user)):
    """
    Ensure the authenticated user's caterer_id matches the 'cid' path param.
    """
    if current_user.caterer_id != cid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this tenant",
        )


@router.get("", response_model=List[schemas.CustomerOut])
def list_customers(
    cid: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name", regex="^(name|created_at)$"),
    sort_dir: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_sql_db),
    _=Depends(check_tenant),
):
    """
    List customers for a given caterer (tenant) with pagination & sorting.
    """
    order_clause = asc(sort_by) if sort_dir == "asc" else desc(sort_by)
    customers = (
        db.query(models.Customer)
        .filter_by(caterer_id=cid)
        .order_by(order_clause)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return customers


@router.post("", response_model=schemas.CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    cid: str,
    dto: schemas.CustomerCreate,
    db: Session = Depends(get_sql_db),
    _=Depends(check_tenant),
):
    """
    Create a new customer under this caterer.
    """
    # Check duplicate phone
    existing = (
        db.query(models.Customer)
        .filter_by(caterer_id=cid, phone=dto.phone)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this phone already exists",
        )

    cust = models.Customer(caterer_id=cid, **dto.model_dump())
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


@router.get("/search", response_model=Optional[schemas.CustomerOut])
def search_customer(
    cid: str,
    phone: str = Query(..., description="Phone number to search"),
    db: Session = Depends(get_sql_db),
    _=Depends(check_tenant),
):
    """
    Search for a customer by exact phone number. Returns one or null.
    """
    return (
        db.query(models.Customer)
        .filter_by(caterer_id=cid, phone=phone)
        .first()
    )


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(
    cid: str,
    customer_id: str,
    db: Session = Depends(get_sql_db),
    _=Depends(check_tenant),
):
    """
    Retrieve a specific customer by ID.
    """
    cust = (
        db.query(models.Customer)
        .filter_by(caterer_id=cid, customer_id=customer_id)
        .first()
    )
    if not cust:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return cust


@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(
    cid: str,
    customer_id: str,
    dto: schemas.CustomerUpdate,
    db: Session = Depends(get_sql_db),
    _=Depends(check_tenant),
):
    """
    Update any of name/phone/email for a customer.
    """
    cust = (
        db.query(models.Customer)
        .filter_by(caterer_id=cid, customer_id=customer_id)
        .first()
    )
    if not cust:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    update_data = dto.model_dump(exclude_unset=True)
    # If phone is being changed, ensure no conflict
    new_phone = update_data.get("phone")
    if new_phone and new_phone != cust.phone:
        conflict = (
            db.query(models.Customer)
            .filter_by(caterer_id=cid, phone=new_phone)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another customer with this phone already exists",
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(cust, field, value)

    db.commit()
    db.refresh(cust)
    return cust


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    cid: str,
    customer_id: str,
    db: Session = Depends(get_sql_db),
    _=Depends(check_tenant),
):
    """
    Delete a customer. If they have existing orders, block deletion.
    """
    cust = (
        db.query(models.Customer)
        .filter_by(caterer_id=cid, customer_id=customer_id)
        .first()
    )
    if not cust:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Check for existing orders
    from app.modules.order.models import Order  # avoid circular import
    existing_order = (
        db.query(Order)
        .filter_by(caterer_id=cid, customer_id=customer_id)
        .first()
    )
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete customer with existing orders",
        )

    db.delete(cust)
    db.commit()
    return None
