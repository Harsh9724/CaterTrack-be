from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

#
# ─── 2.1  MenuCategory Schemas (unchanged) ─────────────────────────────────────
#
class MenuCategoryCreate(BaseModel):
    name: str

class MenuCategoryOut(BaseModel):
    id:          str
    name:        str
    created_at:  datetime
    updated_at:  Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

#
# ─── 2.2  MenuItem Schemas (unchanged) ─────────────────────────────────────────
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
# ─── 2.3  Package Schemas ────────────────────────────────────────────────────
#
class PackageCreate(BaseModel):
    name:             str
    price:            float
    description:      Optional[str]                 = None
    # Each menu entry now holds only name + description
    menu:             Optional[List[dict[str, str]]] = None
    decoration_type:  Optional[str]                  = None
    waiter_count:     Optional[int]                  = None
    pro_couple_count: Optional[int]                  = None

class PackageOut(BaseModel):
    id:               str
    name:             str
    price:            float
    description:      Optional[str]
    menu:             Optional[List[dict[str, Any]]]
    decoration_type:  Optional[str]
    waiter_count:     Optional[int]
    pro_couple_count: Optional[int]
    created_at:       datetime
    updated_at:       Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class FullMenuCategoryOut(MenuCategoryOut):
    items: List[MenuItemOut]
