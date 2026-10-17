from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./resume_screener.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class EvaluationDB(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    candidate_name = Column(String, index=True, nullable=True)
    match_score = Column(Integer)
    matching_skills = Column(Text) # Stored as comma-separated string or JSON string
    missing_skills = Column(Text)
    summary_reasoning = Column(Text)
    recommendation = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)