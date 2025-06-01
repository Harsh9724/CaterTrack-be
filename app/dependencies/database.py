# app/dependencies/database.py
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.cockroach import SessionLocal
from app.db.mongo import get_mongo_db

def get_sql_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo(db=Depends(get_mongo_db)):
    return db
