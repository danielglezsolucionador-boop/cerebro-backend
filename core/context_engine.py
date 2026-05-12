from datetime import datetime, timedelta
from core.database import (
    SessionLocal, ReportModel, GoalModel, PriorityModel,
    ExecutiveMemoryModel, TelegramConversationModel, CEOMemoryModel,
    TimelineModel, TelegramMessageModel
)

def get_operational_context() -> dict:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        recent_reports = db.query(ReportModel).filter(
            ReportModel.created_at >= last_24h
        ).order_by(ReportModel.created_at.desc()).limit(10).all()

        critical_reports = db.query(ReportModel).filter(
            ReportModel.priority == "CRITICAL"
        ).order_by(ReportModel.created_at.desc()).limit(5).all()

        active_goals = db.query(GoalModel).filter(
            GoalModel.status == "ACTIVE"
        ).limit(10).all()

        pending_priorities = db.query(PriorityModel).filter(
            PriorityModel.resolved == False
        ).order_by(PriorityModel.created_at.desc()).limit(10).all()

        executive_memory = db.query(ExecutiveMemoryModel).order_by(
            ExecutiveMemoryModel.importance.desc(),
            ExecutiveMemoryModel.created_at.desc()
        ).limit(10).all()

        ceo_memory = db.query(CEOMemoryModel).order_by(
            CEOMemoryModel.created_at.desc()
        ).limit(10).all()

        recent_timeline = db.query(TimelineModel).filter(
            TimelineModel.created_at >= last_7d
        ).order_by(TimelineModel.created_at.desc()).limit(10).all()

        total_reports = db.query(ReportModel).count()
        total_goals = db.query(GoalModel).count()
        completed_goals = db.query(GoalModel).filter(GoalModel.status == "COMPLETED").count()

        return {
            "timestamp": now.isoformat(),
            "reports": {
                "total": total_reports,
                "recent_24h": [
                    {"agent": r.agent, "message": r.message[:200], "priority": r.priority, "category": r.category, "time": r.created_at.isoformat()}
                    for r in recent_reports
                ],
                "critical": [
                    {"agent": r.agent, "message": r.message[:200], "time": r.created_at.isoformat()}
                    for r in critical_reports
                ],
            },
            "goals": {
                "total": total_goals,
                "completed": completed_goals,
                "active": [
                    {"title": g.title, "priority": g.priority, "status": g.status}
                    for g in active_goals
                ],
            },
            "priorities": {
                "pending": [
                    {"level": p.level, "reason": p.reason[:200]}
                    for p in pending_priorities
                ],
            },
            "executive_memory": [
                {"context_type": m.context_type, "content": m.content[:200], "importance": m.importance}
                for m in executive_memory
            ],
            "ceo_memory": [
                {"category": m.category, "content": m.content[:200]}
                for m in ceo_memory
            ],
            "timeline": [
                {"event_type": t.event_type, "title": t.title, "importance": t.importance, "time": t.created_at.isoformat()}
                for t in recent_timeline
            ],
        }
    except Exception as e:
        print(f"Context engine error: {e}")
        return {}
    finally:
        db.close()

def get_conversation_history(limit: int = 10) -> list:
    db = SessionLocal()
    try:
        records = db.query(TelegramConversationModel).order_by(
            TelegramConversationModel.created_at.desc()
        ).limit(limit).all()
        return [
            {"role": r.role, "message": r.message, "context_type": r.context_type, "time": r.created_at.isoformat()}
            for r in reversed(records)
        ]
    except Exception as e:
        print(f"Conversation history error: {e}")
        return []
    finally:
        db.close()

def save_conversation(role: str, message: str, context_type: str = "operational", metadata: str = ""):
    import uuid
    db = SessionLocal()
    try:
        record = TelegramConversationModel(
            id=str(uuid.uuid4()),
            role=role,
            message=message,
            context_type=context_type,
            meta=metadata,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Save conversation error: {e}")
    finally:
        db.close()

def save_ceo_memory(category: str, content: str, source: str = "conversation"):
    import uuid
    db = SessionLocal()
    try:
        record = CEOMemoryModel(
            id=str(uuid.uuid4()),
            category=category,
            content=content,
            source=source,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Save CEO memory error: {e}")
    finally:
        db.close()

def save_timeline_event(event_type: str, title: str, description: str = "", importance: str = "NORMAL"):
    import uuid
    db = SessionLocal()
    try:
        record = TimelineModel(
            id=str(uuid.uuid4()),
            event_type=event_type,
            title=title,
            description=description,
            importance=importance,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Save timeline error: {e}")
    finally:
        db.close()