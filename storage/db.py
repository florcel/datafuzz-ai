from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
import os

DATABASE_URL = os.getenv("DATAFUZZ_DATABASE_URL", "sqlite:///datafuzz.db")

# select connect_args for sqlite only
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# create engine with pool_pre_ping to be resilient to dropped connections
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    Base.metadata.create_all(bind=engine)