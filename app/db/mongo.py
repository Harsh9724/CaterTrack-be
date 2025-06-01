# app/db/mongo.py
from pymongo import MongoClient
from app.core.config import settings

_client = None

def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client

def get_mongo_db(db_name: str = "catertrack"):
    return get_mongo_client()[db_name]
