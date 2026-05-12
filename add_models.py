addition = """

class ExecutivePriorityModel(Base):
    __tablename__ = "executive_priorities"
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    priority_level = Column(String, default="MEDIUM")
    status = Column(String, default="pending")
    assigned_agent = Column(String)
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class DecisionMemoryModel(Base):
    __tablename__ = "decision_memory"
    id = Column(String, primary_key=True)
    topic = Column(String, index=True)
    decision = Column(Text)
    reasoning = Column(Text)
    related_agent = Column(String)
    tags = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimelineModel(Base):
    __tablename__ = "timeline"
    id = Column(String, primary_key=True)
    event_type = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    source = Column(String)
    importance = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
"""
content = open("core/database.py", "r", encoding="utf-8").read()
open("core/database.py", "w", encoding="utf-8").write(content + addition)
print("OK")
