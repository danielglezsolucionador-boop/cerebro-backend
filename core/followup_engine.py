import uuid
from datetime import datetime, timedelta
from core.database import SessionLocal, ExecutivePriorityModel, TimelineModel

FOLLOWUP_RULES = {
    'CRITICAL': 2,
    'HIGH': 6,
}

def check_followups():
    db = SessionLocal()
    notified = 0
    try:
        now = datetime.utcnow()
        for level, hours in FOLLOWUP_RULES.items():
            threshold = now - timedelta(hours=hours)
            pending = db.query(ExecutivePriorityModel).filter(
                ExecutivePriorityModel.priority_level == level,
                ExecutivePriorityModel.status == 'pending',
                ExecutivePriorityModel.created_at <= threshold,
            ).all()

            for p in pending:
                elapsed = now - p.created_at
                hours_open = int(elapsed.total_seconds() // 3600)
                mins_open = int((elapsed.total_seconds() % 3600) // 60)

                _notify_followup(p, hours_open, mins_open)

                timeline = TimelineModel(
                    id=str(uuid.uuid4()),
                    event_type='followup_ejecutivo',
                    title=f'Follow-up {level} — {p.assigned_agent}',
                    description=f'Sin resolución después de {hours_open}h {mins_open}m',
                    importance=level,
                    created_at=now,
                )
                db.add(timeline)
                notified += 1

        db.commit()
        if notified:
            print(f'[followup_engine] {notified} follow-ups enviados')
    except Exception as e:
        db.rollback()
        print(f'[followup_engine] Error: {e}')
    finally:
        db.close()
    return notified

def _notify_followup(priority, hours_open, mins_open):
    from core.telegram_gateway import notify
    emoji = '🚨' if priority.priority_level == 'CRITICAL' else '🔴'
    text = (
        f'{emoji} <b>FOLLOW-UP EJECUTIVO</b>\n\n'
        f'Prioridad <b>{priority.priority_level}</b> sigue sin resolución.\n\n'
        f'<b>Agente:</b> {priority.assigned_agent}\n'
        f'<b>Problema:</b> {priority.description[:80]}\n'
        f'<b>Tiempo abierto:</b> {hours_open}h {mins_open}m\n\n'
        f'¿Deseas escalar, ignorar o resolver?\n'
        f'Responde: <code>resolver {priority.id[:8]}</code>'
    )
    notify(text)