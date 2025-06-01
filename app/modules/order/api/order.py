# app/modules/order/api/order.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from bson.objectid import ObjectId
from datetime import datetime

from app.dependencies.database import get_sql_db, get_mongo_db
from app.modules.auth.api.deps import get_current_active_user
from app.modules.order import models, schemas
from app.modules.customer.models import Customer

router = APIRouter(
    prefix="/caterer/{cid}",
    tags=["order"],
)


def check_tenant(cid: str, current_user=Depends(get_current_active_user)):
    """
    Ensure the authenticated user's caterer_id matches the path parameter.
    """
    if current_user.caterer_id != cid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


#
# ─── 2.1  List All Orders ─────────────────────────────────────────────────────
#
@router.get(
    "/orders",
    response_model=List[schemas.OrderOut],
)
def list_orders(
    cid: str,
    db: Session = Depends(get_sql_db),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    List all orders for this caterer, each with embedded events fetched from MongoDB.
    """
    # 1) Fetch all order rows from CockroachDB
    orders = db.query(models.Order).filter_by(caterer_id=cid).all()

    # 2) Bulk-fetch events from Mongo where order_id in the returned orders
    col_evt: Collection = mongo_db["events"]
    order_ids = [order.order_id for order in orders]
    raw_events = list(col_evt.find({"order_id": {"$in": order_ids}}))

    # Group events by order_id
    events_by_order: dict[str, List[dict]] = {}
    for doc in raw_events:
        oid = doc["order_id"]
        events_by_order.setdefault(oid, []).append(doc)

    response: List[schemas.OrderOut] = []
    for order in orders:
        # 3) Load associated customer from SQL
        cust: Customer = db.query(Customer).filter_by(customer_id=order.customer_id).first()
        if not cust:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer_out = schemas.CustomerOut(
            customer_id=cust.customer_id,
            name=cust.name,
            phone=cust.phone,
            email=cust.email,
        )

        # 4) Convert Mongo docs to EventOut
        ev_docs = events_by_order.get(order.order_id, [])
        event_out_list: List[schemas.EventOut] = []
        for doc in ev_docs:
            event_out_list.append(
                schemas.EventOut(
                    event_id=str(doc["_id"]),
                    event_type=doc["event_type"],
                    event_date=doc["event_date"],
                    start_time=doc["start_time"],
                    end_time=doc["end_time"],
                    venue=doc["venue"],
                    no_of_guests=doc["no_of_guests"],
                    extra_services=doc.get("extra_services"),
                    menu=doc.get("menu"),
                    total_amount=doc.get("total_amount", 0.0),
                    created_at=doc["created_at"],
                    updated_at=doc.get("updated_at"),
                )
            )

        # 5) Build the OrderOut
        response.append(
            schemas.OrderOut(
                order_id=order.order_id,
                customer=customer_out,
                events=event_out_list,
                grand_total=order.grand_total,
                advance=order.advance,
                due=order.due,
                paid_status=order.paid_status,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
        )

    return response


#
# ─── 2.2  Get Single Order ────────────────────────────────────────────────────
#
@router.get(
    "/orders/{order_id}",
    response_model=schemas.OrderOut,
)
def get_order(
    cid: str,
    order_id: str,
    db: Session = Depends(get_sql_db),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Retrieve a single order (SQL) along with its events (Mongo).
    """
    # 1) Fetch the order row
    order = db.query(models.Order).filter_by(caterer_id=cid, order_id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2) Fetch the customer
    cust: Customer = db.query(Customer).filter_by(customer_id=order.customer_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer_out = schemas.CustomerOut(
        customer_id=cust.customer_id,
        name=cust.name,
        phone=cust.phone,
        email=cust.email,
    )

    # 3) Fetch events for this order
    col_evt: Collection = mongo_db["events"]
    raw_events = list(col_evt.find({"order_id": order_id}))

    event_out_list: List[schemas.EventOut] = []
    for doc in raw_events:
        event_out_list.append(
            schemas.EventOut(
                event_id=str(doc["_id"]),
                event_type=doc["event_type"],
                event_date=doc["event_date"],
                start_time=doc["start_time"],
                end_time=doc["end_time"],
                venue=doc["venue"],
                no_of_guests=doc["no_of_guests"],
                extra_services=doc.get("extra_services"),
                menu=doc.get("menu"),
                total_amount=doc.get("total_amount", 0.0),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at"),
            )
        )

    return schemas.OrderOut(
        order_id=order.order_id,
        customer=customer_out,
        events=event_out_list,
        grand_total=order.grand_total,
        advance=order.advance,
        due=order.due,
        paid_status=order.paid_status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


#
# ─── 2.3  Create Order (Existing Customer) ───────────────────────────────────
#
@router.post(
    "/order",
    response_model=schemas.OrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    cid: str,
    dto: schemas.OrderIn,
    db: Session = Depends(get_sql_db),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Create an order for an existing customer:
    - Insert one Order row in CockroachDB
    - Insert N Event documents in MongoDB
    - Sum each event's total_amount to set grand_total
    """
    # 1) Validate customer exists
    cust: Customer = db.query(Customer).filter_by(
        customer_id=dto.customer_id, caterer_id=cid
    ).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    # 2) Insert the Order row
    order = models.Order(caterer_id=cid, customer_id=dto.customer_id)
    db.add(order)
    db.flush()  # populate order.order_id

    # 3) Insert Event documents in Mongo and accumulate total_amount
    col_evt: Collection = mongo_db["events"]
    now = datetime.utcnow()
    total_sum = 0.0

    event_docs = []
    for e in dto.events:
        if e.total_amount < 0:
            raise HTTPException(
                status_code=400, detail="Event total_amount must be non-negative"
            )
        total_sum += e.total_amount

        doc = {
            "order_id":       order.order_id,
            "caterer_id":     cid,
            "event_type":     e.event_type,
            "event_date":     e.event_date,
            "start_time":     e.start_time,
            "end_time":       e.end_time,
            "venue":          e.venue,
            "no_of_guests":   e.no_of_guests,
            "extra_services": e.extra_services,
            "menu":           e.menu,
            "total_amount":   e.total_amount,
            "created_at":     now,
            "updated_at":     None,
        }
        event_docs.append(doc)

    if event_docs:
        col_evt.insert_many(event_docs)

    # 4) Update the Order's totals
    order.grand_total = total_sum
    order.due = total_sum - order.advance  # advance defaults to 0
    order.paid_status = "UNPAID" if order.due > 0 else "PAID"

    db.commit()
    db.refresh(order)

    # 5) Build and return the OrderOut (similar to get_order)
    customer_out = schemas.CustomerOut(
        customer_id=cust.customer_id,
        name=cust.name,
        phone=cust.phone,
        email=cust.email,
    )
    inserted = list(col_evt.find({"order_id": order.order_id}))
    event_out_list: List[schemas.EventOut] = []
    for doc in inserted:
        event_out_list.append(
            schemas.EventOut(
                event_id=str(doc["_id"]),
                event_type=doc["event_type"],
                event_date=doc["event_date"],
                start_time=doc["start_time"],
                end_time=doc["end_time"],
                venue=doc["venue"],
                no_of_guests=doc["no_of_guests"],
                extra_services=doc.get("extra_services"),
                menu=doc.get("menu"),
                total_amount=doc.get("total_amount", 0.0),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at"),
            )
        )

    return schemas.OrderOut(
        order_id=order.order_id,
        customer=customer_out,
        events=event_out_list,
        grand_total=order.grand_total,
        advance=order.advance,
        due=order.due,
        paid_status=order.paid_status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


#
# ─── 2.4  Create Order with New Customer ─────────────────────────────────────
#
@router.post(
    "/order-with-customer",
    response_model=schemas.OrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_order_with_customer(
    cid: str,
    dto: schemas.OrderWithCustomerIn,
    db: Session = Depends(get_sql_db),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Create a new customer (if needed) and then create the order + events.
    """
    # 1) Lookup existing customer by phone
    cust = db.query(Customer).filter_by(phone=dto.phone, caterer_id=cid).first()
    if not cust:
        cust = Customer(
            caterer_id=cid,
            name=dto.name or "Unnamed",
            phone=dto.phone,
            email=dto.email,
        )
        db.add(cust)
        db.flush()

    # 2) Insert the Order row
    order = models.Order(caterer_id=cid, customer_id=cust.customer_id)
    db.add(order)
    db.flush()

    # 3) Insert Event docs in Mongo and sum total_amount
    col_evt: Collection = mongo_db["events"]
    now = datetime.utcnow()
    total_sum = 0.0

    event_docs = []
    for e in dto.events:
        if e.total_amount < 0:
            raise HTTPException(
                status_code=400, detail="Event total_amount must be non-negative"
            )
        total_sum += e.total_amount

        doc = {
            "order_id":       order.order_id,
            "caterer_id":     cid,
            "event_type":     e.event_type,
            "event_date":     e.event_date,
            "start_time":     e.start_time,
            "end_time":       e.end_time,
            "venue":          e.venue,
            "no_of_guests":   e.no_of_guests,
            "extra_services": e.extra_services,
            "menu":           e.menu,
            "total_amount":   e.total_amount,
            "created_at":     now,
            "updated_at":     None,
        }
        event_docs.append(doc)

    if event_docs:
        col_evt.insert_many(event_docs)

    # 4) Update order totals
    order.grand_total = total_sum
    order.due = total_sum - order.advance
    order.paid_status = "UNPAID" if order.due > 0 else "PAID"

    db.commit()
    db.refresh(order)
    db.refresh(cust)

    # 5) Build response
    customer_out = schemas.CustomerOut(
        customer_id=cust.customer_id,
        name=cust.name,
        phone=cust.phone,
        email=cust.email,
    )
    inserted = list(col_evt.find({"order_id": order.order_id}))
    event_out_list: List[schemas.EventOut] = []
    for doc in inserted:
        event_out_list.append(
            schemas.EventOut(
                event_id=str(doc["_id"]),
                event_type=doc["event_type"],
                event_date=doc["event_date"],
                start_time=doc["start_time"],
                end_time=doc["end_time"],
                venue=doc["venue"],
                no_of_guests=doc["no_of_guests"],
                extra_services=doc.get("extra_services"),
                menu=doc.get("menu"),
                total_amount=doc.get("total_amount", 0.0),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at"),
            )
        )

    return schemas.OrderOut(
        order_id=order.order_id,
        customer=customer_out,
        events=event_out_list,
        grand_total=order.grand_total,
        advance=order.advance,
        due=order.due,
        paid_status=order.paid_status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


#
# ─── 2.5  Update a Single Event ───────────────────────────────────────────────
#
@router.put(
    "/orders/{order_id}/events/{event_id}",
    response_model=schemas.EventOut,
)
def update_event(
    cid: str,
    order_id: str,
    event_id: str,
    dto: schemas.EventUpdate,
    db: Session = Depends(get_sql_db),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Update fields of a single event document in Mongo.
    """
    # 1) Confirm that the Order exists and belongs to this tenant
    order = db.query(models.Order).filter_by(caterer_id=cid, order_id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2) Locate the event in Mongo and ensure it belongs to this order & tenant
    col_evt: Collection = mongo_db["events"]
    try:
        oid = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event_id format")

    existing = col_evt.find_one({"_id": oid, "order_id": order_id, "caterer_id": cid})
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")

    # 3) Build the update dictionary from non‐unset fields
    update_data = dto.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # If total_amount is being updated, ensure it’s non-negative
    if "total_amount" in update_data and update_data["total_amount"] < 0:
        raise HTTPException(status_code=400, detail="total_amount must be non-negative")

    # Set the updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()

    # 4) Perform the update in Mongo
    result = col_evt.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update event")

    # 5) Re-fetch the updated document
    doc = col_evt.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=500, detail="Event disappeared after update")

    return schemas.EventOut(
        event_id=str(doc["_id"]),
        event_type=doc["event_type"],
        event_date=doc["event_date"],
        start_time=doc["start_time"],
        end_time=doc["end_time"],
        venue=doc["venue"],
        no_of_guests=doc["no_of_guests"],
        extra_services=doc.get("extra_services"),
        menu=doc.get("menu"),
        total_amount=doc.get("total_amount", 0.0),
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at"),
    )


#
# ─── 2.6  Delete a Single Event ────────────────────────────────────────────────
#
@router.delete(
    "/orders/{order_id}/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event(
    cid: str,
    order_id: str,
    event_id: str,
    db: Session = Depends(get_sql_db),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Delete one event document from Mongo.
    """
    # 1) Verify the Order exists for this tenant
    order = db.query(models.Order).filter_by(caterer_id=cid, order_id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2) Ensure the event exists in Mongo under this order & tenant
    col_evt: Collection = mongo_db["events"]
    try:
        oid = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event_id format")

    existing = col_evt.find_one({"_id": oid, "order_id": order_id, "caterer_id": cid})
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")

    # 3) Delete it
    result = col_evt.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete event")

    # 4) Return 204 No Content
    return None
