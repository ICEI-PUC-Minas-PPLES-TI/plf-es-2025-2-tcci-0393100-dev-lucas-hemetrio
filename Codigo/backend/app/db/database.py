from neomodel import config
from app.core.config import settings

def connect_to_db():
    config.DATABASE_URL = settings.NEO4J_URL