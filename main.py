from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import uuid

from core.database import init_db, SessionLocal, UserModel, AgentModel, ReportModel, ExecutiveMemoryModel, PriorityModel, GoalModel, EventModel, ExecutivePriorityModel, DecisionMemoryModel, TimelineModel
from core.auth import get_current_user, get_admin_user, init_default_admin, create_access_token, verify_password, get_user
from core.telegram_gateway import notify_report, notify_goal, notify_alert

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="CEREBRO Executive Backend", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cerebro.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from core.telegram_handler import build_app as build_telegram_app
import asyncio

telegram_app = None

@app.on_event("startup")
async def startup():
    global telegram_app
    init_db()
    init_default_admin()
    telegram_app = build_telegram_app()
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    print("CEREBRO Backend v1.0 - Online")

@app.on_event("shutdown")
async def shutdown():
    global telegram_app
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

@app.get("/api/v1/health")
async def health():
    return {
        "status": "OPERATIONAL",
        "engine": "CEREBRO Executive Backend v1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.post("/api/v1/auth/login")
async def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

@app.post("/api/v1/agents/report")
async def agent_report(payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        record = ReportModel(
            id=str(uuid.uuid4()),
            agent=payload.get("agent", "unknown"),
            message=str(payload.get("message", payload.get("content", ""))),
            category=payload.get("category", "GENERAL"),
            priority=payload.get("priority", "NORMAL"),
            recommended_action=payload.get("recommended_action", ""),
            status=payload.get("status", "PENDING"),
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        notify_report(record.agent, record.message, record.priority)
        return {"id": record.id, "status": "saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/v1/reports")
async def get_reports(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(ReportModel).order_by(ReportModel.created_at.desc()).limit(50).all()
        return [{"id": r.id, "agent": r.agent, "message": r.message, "category": r.category, "priority": r.priority, "status": r.status, "created_at": r.created_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/api/v1/memory")
async def get_memory(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(ExecutiveMemoryModel).order_by(ExecutiveMemoryModel.created_at.desc()).limit(50).all()
        return [{"id": r.id, "context_type": r.context_type, "content": r.content, "source": r.source, "importance": r.importance, "created_at": r.created_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/api/v1/goals")
async def get_goals(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(GoalModel).order_by(GoalModel.created_at.desc()).limit(50).all()
        return [{"id": r.id, "title": r.title, "status": r.status, "priority": r.priority, "created_at": r.created_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.post("/api/v1/goals")
async def create_goal(payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        record = GoalModel(
            id=str(uuid.uuid4()),
            title=payload.get("title", ""),
            status=payload.get("status", "ACTIVE"),
            priority=payload.get("priority", "MEDIUM"),
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        return {"id": record.id, "status": "saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/v1/admin/reset-admin")
async def reset_admin():
    from core.auth import create_user
    db = SessionLocal()
    try:
        db.query(UserModel).filter(UserModel.username == "daniel").delete()
        db.commit()
    finally:
        db.close()
    create_user("daniel", "daniel.glez.solucionador@gmail.com", "cerebro24", is_admin=True)
    return {"status": "admin reset ok"}

@app.post("/api/v1/priorities")
async def create_priority(payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        from core.context_engine import save_timeline_event
        record = ExecutivePriorityModel(
            id=str(uuid.uuid4()),
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            category=payload.get("category", "GENERAL"),
            priority_level=payload.get("priority_level", "MEDIUM"),
            status="pending",
            assigned_agent=payload.get("assigned_agent", ""),
            due_date=datetime.fromisoformat(payload["due_date"]) if payload.get("due_date") else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        save_timeline_event("priority_created", record.title, record.description, record.priority_level)
        from core.telegram_gateway import notify_alert
        notify_alert(f"Nueva prioridad creada: {record.title} [{record.priority_level}]")
        return {"id": record.id, "status": "created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/v1/priorities")
async def get_priorities(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(ExecutivePriorityModel).order_by(ExecutivePriorityModel.created_at.desc()).limit(50).all()
        return [{"id": r.id, "title": r.title, "description": r.description, "category": r.category, "priority_level": r.priority_level, "status": r.status, "assigned_agent": r.assigned_agent, "due_date": r.due_date.isoformat() if r.due_date else None, "created_at": r.created_at.isoformat(), "updated_at": r.updated_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.patch("/api/v1/priorities/{priority_id}")
async def update_priority(priority_id: str, payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        from core.context_engine import save_timeline_event
        record = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.id == priority_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Priority not found")
        for field in ["title", "description", "category", "priority_level", "status", "assigned_agent"]:
            if field in payload:
                setattr(record, field, payload[field])
        record.updated_at = datetime.utcnow()
        db.commit()
        if payload.get("status") == "completed":
            save_timeline_event("priority_completed", record.title, "", "HIGH")
        return {"id": record.id, "status": record.status}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/v1/decisions")
async def create_decision(payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        from core.context_engine import save_timeline_event
        record = DecisionMemoryModel(
            id=str(uuid.uuid4()),
            topic=payload.get("topic", ""),
            decision=payload.get("decision", ""),
            reasoning=payload.get("reasoning", ""),
            related_agent=payload.get("related_agent", ""),
            tags=payload.get("tags", ""),
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        save_timeline_event("decision_made", record.topic, record.decision[:100], "NORMAL")
        return {"id": record.id, "status": "saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/v1/decisions")
async def get_decisions(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(DecisionMemoryModel).order_by(DecisionMemoryModel.created_at.desc()).limit(50).all()
        return [{"id": r.id, "topic": r.topic, "decision": r.decision, "reasoning": r.reasoning, "related_agent": r.related_agent, "tags": r.tags, "created_at": r.created_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/api/v1/decisions/search")
async def search_decisions(q: str, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(DecisionMemoryModel).filter(
            DecisionMemoryModel.topic.ilike(f"%{q}%") |
            DecisionMemoryModel.decision.ilike(f"%{q}%") |
            DecisionMemoryModel.tags.ilike(f"%{q}%")
        ).order_by(DecisionMemoryModel.created_at.desc()).limit(10).all()
        return [{"id": r.id, "topic": r.topic, "decision": r.decision, "reasoning": r.reasoning, "tags": r.tags, "created_at": r.created_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/api/v1/timeline")
async def get_timeline(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(TimelineModel).order_by(TimelineModel.created_at.desc()).limit(50).all()
        return [{"id": r.id, "event_type": r.event_type, "title": r.title, "description": r.description, "importance": r.importance, "created_at": r.created_at.isoformat()} for r in records]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/api/v1/summary")
async def get_summary(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        from datetime import timedelta
        now = datetime.utcnow()
        total_reports = db.query(ReportModel).count()
        pending_priorities = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.status == "pending").count()
        critical_priorities = db.query(ExecutivePriorityModel).filter(
            ExecutivePriorityModel.priority_level == "CRITICAL",
            ExecutivePriorityModel.status == "pending"
        ).count()
        total_decisions = db.query(DecisionMemoryModel).count()
        recent_reports = db.query(ReportModel).filter(
            ReportModel.created_at >= now - timedelta(hours=24)
        ).count()
        overdue = db.query(ExecutivePriorityModel).filter(
            ExecutivePriorityModel.status == "pending",
            ExecutivePriorityModel.due_date < now
        ).count()
        return {
            "total_reports": total_reports,
            "pending_priorities": pending_priorities,
            "critical_priorities": critical_priorities,
            "total_decisions": total_decisions,
            "recent_reports_24h": recent_reports,
            "overdue_priorities": overdue,
            "timestamp": now.isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
