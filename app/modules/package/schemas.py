# app/modules/package/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

#
# ─── 2.1  MenuCategory Schemas ─────────────────────────────────────────────
#
class MenuCategoryCreate(BaseModel):
    name: str


class MenuCategoryOut(BaseModel):
    id:          str
    name:        str
    created_at:  datetime
    updated_at:  Optional[datetime]

    # In Pydantic v2, `from_attributes=True` allows reading plain dicts
    model_config = ConfigDict(from_attributes=True)


#
# ─── 2.2  MenuItem Schemas ─────────────────────────────────────────────────
#
class MenuItemCreate(BaseModel):
    category_id: str
    name:        str
    description: Optional[str] = None


class MenuItemOut(BaseModel):
    id:          str
    category_id: str
    name:        str
    description: Optional[str]
    created_at:  datetime
    updated_at:  Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


#
# ─── 2.3  Package Schemas ──────────────────────────────────────────────────
#
class PackageCreate(BaseModel):
    name:        str
    price:       float
    description: Optional[str]                 = None
    menu:        Optional[List[dict[str, Any]]] = None
    # Example: [{"category_id": "...", "item_id": "...", "quantity": 2}, ...]


class PackageOut(BaseModel):
    id:          str
    name:        str
    price:       float
    description: Optional[str]
    menu:        Optional[List[dict[str, Any]]]
    created_at:  datetime
    updated_at:  Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class FullMenuCategoryOut(MenuCategoryOut):
    items: List[MenuItemOut]