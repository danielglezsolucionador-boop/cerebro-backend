from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import uuid

from core.database import init_db, SessionLocal, UserModel, AgentModel, ReportModel, ExecutiveMemoryModel, PriorityModel, GoalModel, EventModel
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)