from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(String, nullable=True)
    results = relationship("Result", back_populates="run")

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    endpoint = Column(String)
    method = Column(String)
    payload = Column(JSON)
    status_code = Column(Integer, nullable=True)
    latency = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    run = relationship("Run", back_populates="results")