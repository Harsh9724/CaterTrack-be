# app/modules/package/api/menu_import.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List
import csv
from io import StringIO
from app.dependencies.database import get_mongo_db
from pymongo.collection import Collection
from bson.objectid import ObjectId
from app.modules.auth.api.deps import get_current_active_user
from datetime import datetime

router = APIRouter(
    prefix="/caterer/{cid}/menu",
    tags=["menu"],
)

def check_tenant(cid: str, current_user=Depends(get_current_active_user)):
    if current_user.caterer_id != cid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/import")
async def import_menu(
    cid: str,
    file: UploadFile = File(...),    # ← FastAPI will look for “file” in multipart/form-data
    mongo_db = Depends(get_mongo_db),
    _ = Depends(check_tenant),
):
    """
    Expect a CSV with columns: Category,Item,Description
    Creates any new categories in `menu_categories` and new items in `menu_items`.
    Returns a summary of how many categories and items were added.
    """
    # 1) Read and decode the CSV
    contents = await file.read()
    text = contents.decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    if not {"Category", "Item", "Description"}.issubset(reader.fieldnames or []):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "CSV must have exactly headers: Category,Item,Description")

    col_cat: Collection = mongo_db["menu_categories"]
    col_itm: Collection = mongo_db["menu_items"]

    categories_added = 0
    items_added = 0

    # 2) For each row: upsert category, then upsert item
    for row in reader:
        cat_name = row["Category"].strip()
        itm_name = row["Item"].strip()
        itm_desc = row["Description"].strip()

        # 2a) Category: if it doesn’t exist, insert
        cat_doc = col_cat.find_one({"caterer_id": cid, "name": cat_name})
        if not cat_doc:
            new_cat = {
                "caterer_id": cid,
                "name": cat_name,
                "created_at": datetime.utcnow(),
                "updated_at": None,
            }
            result = col_cat.insert_one(new_cat)
            cat_id_str = str(result.inserted_id)
            categories_added += 1
        else:
            cat_id_str = str(cat_doc["_id"])

        # 2b) Item: if it doesn’t exist in that category, insert
        existing_item = col_itm.find_one({
            "caterer_id": cid,
            "category_id": cat_id_str,
            "name": itm_name,
        })
        if not existing_item:
            new_item = {
                "caterer_id": cid,
                "category_id": cat_id_str,
                "name": itm_name,
                "description": itm_desc,
                "created_at": datetime.utcnow(),
                "updated_at": None,
            }
            col_itm.insert_one(new_item)
            items_added += 1

    return {
        "message": "Import completed.",
        "categories_added": categories_added,
        "items_added": items_added,
    }
