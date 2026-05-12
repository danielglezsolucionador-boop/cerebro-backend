endpoints = """

@app.post("/api/v1/priorities")
async def create_priority(payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        p = ExecutivePriorityModel(
            id=str(uuid.uuid4()),
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            category=payload.get("category", "GENERAL"),
            priority_level=payload.get("priority_level", "MEDIUM"),
            status="pending",
            assigned_agent=payload.get("assigned_agent", ""),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(p)
        db.commit()
        return {"id": p.id, "title": p.title, "status": p.status}
    finally:
        db.close()

@app.get("/api/v1/priorities")
async def get_priorities(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        items = db.query(ExecutivePriorityModel).order_by(ExecutivePriorityModel.created_at.desc()).all()
        return [{"id": i.id, "title": i.title, "status": i.status, "priority_level": i.priority_level, "created_at": i.created_at.isoformat() if i.created_at else None} for i in items]
    finally:
        db.close()

@app.patch("/api/v1/priorities/{priority_id}")
async def update_priority(priority_id: str, payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        p = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.id == priority_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        for key in ["title", "description", "status", "priority_level", "assigned_agent"]:
            if key in payload:
                setattr(p, key, payload[key])
        p.updated_at = datetime.utcnow()
        db.commit()
        return {"id": p.id, "status": p.status}
    finally:
        db.close()

@app.post("/api/v1/decisions")
async def save_decision(payload: dict, current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        d = DecisionMemoryModel(
            id=str(uuid.uuid4()),
            topic=payload.get("topic", ""),
            decision=payload.get("decision", ""),
            reasoning=payload.get("reasoning", ""),
            related_agent=payload.get("related_agent", ""),
            tags=payload.get("tags", ""),
            created_at=datetime.utcnow()
        )
        db.add(d)
        db.commit()
        return {"id": d.id, "topic": d.topic}
    finally:
        db.close()

@app.get("/api/v1/decisions")
async def get_decisions(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        items = db.query(DecisionMemoryModel).order_by(DecisionMemoryModel.created_at.desc()).limit(50).all()
        return [{"id": i.id, "topic": i.topic, "decision": i.decision, "reasoning": i.reasoning, "tags": i.tags, "created_at": i.created_at.isoformat() if i.created_at else None} for i in items]
    finally:
        db.close()

@app.get("/api/v1/timeline")
async def get_timeline(current_user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        items = db.query(TimelineModel).order_by(TimelineModel.created_at.desc()).limit(100).all()
        return [{"id": i.id, "event_type": i.event_type, "title": i.title, "source": i.source, "importance": i.importance, "created_at": i.created_at.isoformat() if i.created_at else None} for i in items]
    finally:
        db.close()
"""
content = open("main.py", "r", encoding="utf-8").read()
open("main.py", "w", encoding="utf-8").write(content + endpoints)
print("OK")
