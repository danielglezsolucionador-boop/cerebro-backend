import os
import json
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cerebro.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentModel(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    status = Column(String, default="ACTIVE")
    last_report = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReportModel(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    agent = Column(String, index=True)
    priority = Column(String, default="NORMAL")
    category = Column(String)
    message = Column(Text)
    recommended_action = Column(Text)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

class ExecutiveMemoryModel(Base):
    __tablename__ = "executive_memory"
    id = Column(String, primary_key=True)
    context_type = Column(String, index=True)
    content = Column(Text)
    source = Column(String)
    importance = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

class PriorityModel(Base):
    __tablename__ = "priorities"
    id = Column(String, primary_key=True)
    level = Column(String)
    reason = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoalModel(Base):
    __tablename__ = "goals"
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    target = Column(String)
    current_value = Column(String)
    status = Column(String, default="ACTIVE")
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventModel(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    source = Column(String, index=True)
    event_type = Column(String)
    payload = Column(Text)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TelegramMessageModel(Base):
    __tablename__ = "telegram_messages"
    id = Column(String, primary_key=True)
    sender = Column(String, index=True)
    message = Column(Text)
    direction = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class TelegramConversationModel(Base):
    __tablename__ = "telegram_conversations"
    id = Column(String, primary_key=True)
    role = Column(String, index=True)
    message = Column(Text)
    context_type = Column(String)
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class CEOMemoryModel(Base):
    __tablename__ = "ceo_memory"
    id = Column(String, primary_key=True)
    category = Column(String, index=True)
    content = Column(Text)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimelineModel(Base):
    __tablename__ = "timeline"
    id = Column(String, primary_key=True)
    event_type = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    importance = Column(String, default="NORMAL")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
