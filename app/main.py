# app/main.py
import app.core.patches
import multiprocessing
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.db.cockroach import Base, engine

# import your auth router
from app.modules.auth.api.auth import router as auth_router
from app.modules.caterer.api.profile import router as profile_router
from app.modules.customer.api.customer import router as customer_router
from app.modules.package.api.package import router as package_router
from app.modules.order.api.order import router as order_router

from app.modules.package.api.menu_import import router as menu_import_router

# create all SQL tables (dev only; use Alembic in prod)
# Base.metadata.drop_all(bind=engine)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CaterTrack Auth Service")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# ────── ENABLE CORS ─────────────────────────────────────────────────────────
# Allow calls from your frontend (http://localhost:3000)
origins = [
    "http://localhost:3000",
    "https://www.catertrack.in",
    "https://catertrack.in",
    # If you ever deploy to another domain, add it here, e.g.:
    # "https://my-production-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,               # <— which origins are allowed
    allow_credentials=True,              # <— allow cookies/auth
    allow_methods=["*"],                 # <— allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                 # <— allow any headers (e.g. Authorization)
)
# ─────────────────────────────────────────────────────────────────────────────

# include the auth microservice router
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(customer_router)
app.include_router(package_router)
app.include_router(order_router)

app.include_router(menu_import_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,                     # dev only
        workers=multiprocessing.cpu_count(),
    )
