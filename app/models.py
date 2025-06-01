# app/models.py
from app.db.cockroach import Base

from app.modules.auth.models import User, Invite, PasswordReset
from app.modules.caterer.models import Caterer
from app.modules.customer.models import Customer
from app.modules.order.models import Order
# from app.modules.package.models import MenuCategory, MenuItem, Package

# No code needed; importing registers them with Base.metadata
