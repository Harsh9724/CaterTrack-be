# app/modules/package/api/package.py

from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from pymongo.collection import Collection
from bson.objectid import ObjectId
from datetime import datetime

from app.dependencies.database import get_mongo_db
from app.modules.auth.api.deps import get_current_active_user
from app.modules.package import schemas

router = APIRouter(
    prefix="/caterer/{cid}",
    tags=["package", "menu"],
)


def check_tenant(cid: str, current_user=Depends(get_current_active_user)):
    """
    Ensure the authenticated user belongs to this tenant (caterer).
    """
    if current_user.caterer_id != cid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

# ─── 3.1  Menu Category Endpoints ──────────────────────────────────────────
#
@router.post(
    "/menu/category",
    response_model=schemas.MenuCategoryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_category(
    cid: str,
    dto: schemas.MenuCategoryCreate,
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Insert a new menu category document under this caterer.
    """
    col: Collection = mongo_db["menu_categories"]

    # Prevent duplicate category name under the same caterer
    if col.find_one({"caterer_id": cid, "name": dto.name}):
        raise HTTPException(status_code=400, detail="Category already exists")

    now = datetime.utcnow()
    doc = {
        "caterer_id": cid,
        "name": dto.name,
        "created_at": now,
        "updated_at": None,
    }
    result = col.insert_one(doc)
    return {
        "id": str(result.inserted_id),
        "name": dto.name,
        "created_at": now,
        "updated_at": None,
    }


@router.get(
    "/menu/category",
    response_model=List[schemas.MenuCategoryOut],
)
def list_menu_categories(
    cid: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("name", regex="^(name|created_at)$"),
    sort_dir: str = Query("asc", regex="^(asc|desc)$"),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    List categories with pagination & sorting.
    """
    col: Collection = mongo_db["menu_categories"]
    sort_field = sort_by
    sort_direction = 1 if sort_dir == "asc" else -1

    cursor = (
        col.find({"caterer_id": cid})
        .sort(sort_field, sort_direction)
        .skip(skip)
        .limit(limit)
    )
    results: List[dict] = list(cursor)
    response = []
    for doc in results:
        response.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "created_at": doc["created_at"],
                "updated_at": doc.get("updated_at"),
            }
        )
    return response


#
# ─── 3.2  Menu Item Endpoints ───────────────────────────────────────────────
#
@router.post(
    "/menu/item",
    response_model=schemas.MenuItemOut,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item(
    cid: str,
    dto: schemas.MenuItemCreate,
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Insert a new menu item under a given category for this caterer.
    """
    col_cat: Collection = mongo_db["menu_categories"]
    col_itm: Collection = mongo_db["menu_items"]

    # 1) Validate that category exists and belongs to this caterer
    try:
        cat_obj = ObjectId(dto.category_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid category_id format")

    cat_doc = col_cat.find_one({"_id": cat_obj, "caterer_id": cid})
    if not cat_doc:
        raise HTTPException(status_code=404, detail="Category not found")

    # 2) Prevent duplicate item name under the same category
    if col_itm.find_one(
        {
            "caterer_id": cid,
            "category_id": dto.category_id,
            "name": dto.name,
        }
    ):
        raise HTTPException(status_code=400, detail="Menu item already exists")

    now = datetime.utcnow()
    doc = {
        "caterer_id": cid,
        "category_id": dto.category_id,
        "name": dto.name,
        "description": dto.description,
        "created_at": now,
        "updated_at": None,
    }
    result = col_itm.insert_one(doc)
    return {
        "id": str(result.inserted_id),
        "category_id": dto.category_id,
        "name": dto.name,
        "description": dto.description,
        "created_at": now,
        "updated_at": None,
    }


@router.get(
    "/menu/item",
    response_model=List[schemas.MenuItemOut],
)
def list_menu_items(
    cid: str,
    category_id: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("name", regex="^(name|created_at)$"),
    sort_dir: str = Query("asc", regex="^(asc|desc)$"),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    List menu items, optionally filtered by category_id, with pagination & sorting.
    """
    col_itm: Collection = mongo_db["menu_items"]
    query: dict = {"caterer_id": cid}

    if category_id:
        # Validate category_id format
        try:
            _ = ObjectId(category_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid category_id format")

        query["category_id"] = category_id

    sort_field = sort_by
    sort_direction = 1 if sort_dir == "asc" else -1

    cursor = (
        col_itm.find(query)
        .sort(sort_field, sort_direction)
        .skip(skip)
        .limit(limit)
    )
    results: List[dict] = list(cursor)
    response = []
    for doc in results:
        response.append(
            {
                "id": str(doc["_id"]),
                "category_id": doc["category_id"],
                "name": doc["name"],
                "description": doc.get("description"),
                "created_at": doc["created_at"],
                "updated_at": doc.get("updated_at"),
            }
        )
    return response


#
# ─── 3.3  Package Endpoints ─────────────────────────────────────────────────
#
@router.post(
    "/packages",
    response_model=schemas.PackageOut,
    status_code=status.HTTP_201_CREATED,
)
def create_package(
    cid: str,
    dto: schemas.PackageCreate,
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Insert a new package for this caterer.
    """
    col_pkg: Collection = mongo_db["packages"]

    # Ensure package name is unique under this tenant
    if col_pkg.find_one({"caterer_id": cid, "name": dto.name}):
        raise HTTPException(status_code=400, detail="Package name already exists")

    now = datetime.utcnow()
    doc = {
        "caterer_id": cid,
        "name": dto.name,
        "price": dto.price,
        "description": dto.description,
        "menu": dto.menu,  # optional list of {category_id, item_id, quantity}
        "created_at": now,
        "updated_at": None,
    }
    result = col_pkg.insert_one(doc)
    return {
        "id": str(result.inserted_id),
        "name": doc["name"],
        "price": doc["price"],
        "description": doc.get("description"),
        "menu": doc.get("menu"),
        "created_at": doc["created_at"],
        "updated_at": None,
    }


@router.get(
    "/packages",
    response_model=List[schemas.PackageOut],
)
def list_packages(
    cid: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("name", regex="^(name|created_at)$"),
    sort_dir: str = Query("asc", regex="^(asc|desc)$"),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    List packages with pagination & sorting.
    """
    col_pkg: Collection = mongo_db["packages"]
    sort_field = sort_by
    sort_direction = 1 if sort_dir == "asc" else -1

    cursor = (
        col_pkg.find({"caterer_id": cid})
        .sort(sort_field, sort_direction)
        .skip(skip)
        .limit(limit)
    )
    results: List[dict] = list(cursor)
    response = []
    for doc in results:
        response.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "price": doc["price"],
                "description": doc.get("description"),
                "menu": doc.get("menu"),
                "created_at": doc["created_at"],
                "updated_at": doc.get("updated_at"),
            }
        )
    return response


#
# ─── 3.4  Full Nested Menu Endpoint ──────────────────────────────────────────
#
@router.get(
    "/menu",
    response_model=List[schemas.FullMenuCategoryOut],
)
def list_full_menu(
    cid: str,
    skip_cat: Optional[int] = Query(
        0, ge=0, description="Number of categories to skip"
    ),
    limit_cat: Optional[int] = Query(
        50, ge=1, le=100, description="Max categories to return"
    ),
    skip_item: Optional[int] = Query(
        0, ge=0, description="Number of items to skip per category"
    ),
    limit_item: Optional[int] = Query(
        100, ge=1, le=500, description="Max items to return per category"
    ),
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    List all menu categories *and* their items, nested in one response.
    Pagination params:
      - skip_cat, limit_cat: apply to categories
      - skip_item, limit_item: apply to items within each category
    """
    col_cat: Collection = mongo_db["menu_categories"]
    col_itm: Collection = mongo_db["menu_items"]

    # 1) Fetch categories with pagination & sorted by name ascending
    cursor_cat = (
        col_cat.find({"caterer_id": cid})
        .sort("name", 1)
        .skip(skip_cat)
        .limit(limit_cat)
    )
    categories = list(cursor_cat)

    response: List[dict] = []
    for cat_doc in categories:
        cat_id_str = str(cat_doc["_id"])
        # 2) For each category, fetch its items with pagination & sorting by name ascending
        cursor_itm = (
            col_itm.find({"caterer_id": cid, "category_id": cat_id_str})
            .sort("name", 1)
            .skip(skip_item)
            .limit(limit_item)
        )
        items = list(cursor_itm)

        # Transform item documents into the MenuItemOut shape
        item_list = []
        for itm in items:
            item_list.append(
                {
                    "id": str(itm["_id"]),
                    "category_id": itm["category_id"],
                    "name": itm["name"],
                    "description": itm.get("description"),
                    "created_at": itm["created_at"],
                    "updated_at": itm.get("updated_at"),
                }
            )

        # Append the category + nested items
        response.append(
            {
                "id": cat_id_str,
                "name": cat_doc["name"],
                "created_at": cat_doc["created_at"],
                "updated_at": cat_doc.get("updated_at"),
                "items": item_list,
            }
        )

    return response


@router.delete(
    "/menu/item/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu_item(
    cid: str,
    item_id: str,
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Delete a single menu item under this caterer.
    """
    col_itm: Collection = mongo_db["menu_items"]

    # Validate item_id format
    try:
        itm_obj = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item_id format")

    # Ensure the item exists and belongs to this caterer
    itm_doc = col_itm.find_one({"_id": itm_obj, "caterer_id": cid})
    if not itm_doc:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Delete the item
    col_itm.delete_one({"_id": itm_obj, "caterer_id": cid})

    return None  # 204 No Content

@router.delete(
    "/menu/category/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu_category(
    cid: str,
    category_id: str,
    mongo_db=Depends(get_mongo_db),
    _=Depends(check_tenant),
):
    """
    Delete a category and all its items under this caterer.
    """
    col_cat: Collection = mongo_db["menu_categories"]
    col_itm: Collection = mongo_db["menu_items"]

    # Validate category_id format
    try:
        cat_obj = ObjectId(category_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid category_id format")

    # Ensure this category exists and belongs to this caterer
    cat_doc = col_cat.find_one({"_id": cat_obj, "caterer_id": cid})
    if not cat_doc:
        raise HTTPException(status_code=404, detail="Category not found")

    # 1) Delete all items belonging to this category
    col_itm.delete_many({"caterer_id": cid, "category_id": category_id})

    # 2) Delete the category itself
    col_cat.delete_one({"_id": cat_obj, "caterer_id": cid})

    return None  # 204 No Content
