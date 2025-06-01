# # app/modules/package/models.py

# import uuid
# from sqlalchemy import (
#     Column, String, DateTime, ForeignKey, Numeric, JSON, UniqueConstraint
# )
# from sqlalchemy.sql import func
# from app.db.cockroach import Base

# ### 3.1 MenuCategory
# class MenuCategory(Base):
#     __tablename__ = "menu_category"
#     id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     caterer_id  = Column(String, ForeignKey("caterers.id"), nullable=False)
#     name        = Column(String, nullable=False)
#     created_at  = Column(DateTime, server_default=func.now())
#     updated_at  = Column(DateTime, onupdate=func.now())

#     __table_args__ = (
#         UniqueConstraint("caterer_id", "name", name="uq_menu_cat_caterer_name"),
#     )


# ### 3.2 MenuItem
# class MenuItem(Base):
#     __tablename__ = "menu_item"
#     id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     caterer_id   = Column(String, ForeignKey("caterers.id"), nullable=False)
#     category_id  = Column(String, ForeignKey("menu_category.id"), nullable=False)
#     name         = Column(String, nullable=False)
#     description  = Column(String, nullable=True)
#     created_at   = Column(DateTime, server_default=func.now())
#     updated_at   = Column(DateTime, onupdate=func.now())

#     __table_args__ = (
#         UniqueConstraint("caterer_id", "category_id", "name", name="uq_item_caterer_cat_name"),
#     )


# ### 3.3 Package
# class Package(Base):
#     __tablename__ = "package"
#     id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     caterer_id   = Column(String, ForeignKey("caterers.id"), nullable=False)
#     name         = Column(String, nullable=False)
#     price        = Column(Numeric(10, 2), nullable=False)
#     description  = Column(String, nullable=True)
#     # embed selected items (JSON array of {category_id, item_id, quantity})
#     menu         = Column(JSON, nullable=True)
#     created_at   = Column(DateTime, server_default=func.now())
#     updated_at   = Column(DateTime, onupdate=func.now())

#     __table_args__ = (
#         UniqueConstraint("caterer_id", "name", name="uq_package_caterer_name"),
#     )
