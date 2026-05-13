import uuid
from datetime import datetime

CRITICAL_KEYWORDS = [
    'jailbreak', 'injection', 'breach', 'hack', 'ataque', 'compromised',
    'critico', 'crítico', 'critical', 'emergency', 'emergencia', 'down',
    'caido', 'caído', 'fallo total', 'system failure', 'data loss'
]

HIGH_KEYWORDS = [
    'error', 'fallo', 'failure', 'multiple', 'múltiple', 'timeout',
    'exception', 'crash', 'loop', 'blocked', 'bloqueado', 'atrasado',
    'overdue', 'escalate', 'escalar', 'urgente', 'urgent'
]

MEDIUM_KEYWORDS = [
    'warning', 'advertencia', 'delay', 'retraso', 'objetivo', 'goal',
    'pending', 'pendiente', 'review', 'revisar', 'check', 'verificar'
]

CRITICAL_AGENTS = ['sentinela', 'security', 'seguridad', 'threat']
HIGH_AGENTS = ['backend', 'infra', 'database']

def classify_priority(agent: str, message: str, category: str) -> str:
    text = (message + ' ' + category + ' ' + agent).lower()

    for kw in CRITICAL_KEYWORDS:
        if kw in text:
            return 'CRITICAL'

    if any(a in agent.lower() for a in CRITICAL_AGENTS):
        for kw in HIGH_KEYWORDS:
            if kw in text:
                return 'CRITICAL'

    for kw in HIGH_KEYWORDS:
        if kw in text:
            return 'HIGH'

    for kw in MEDIUM_KEYWORDS:
        if kw in text:
            return 'MEDIUM'

    return 'LOW'

def build_reasoning(agent: str, message: str, category: str, level: str) -> str:
    text = (message + ' ' + category + ' ' + agent).lower()

    if level == 'CRITICAL':
        matched = [kw for kw in CRITICAL_KEYWORDS if kw in text]
        return f"Clasificado CRITICAL — keywords detectados: {matched or ['agente critico']}"
    elif level == 'HIGH':
        matched = [kw for kw in HIGH_KEYWORDS if kw in text]
        return f"Clasificado HIGH — keywords detectados: {matched or ['agente de alto impacto']}"
    elif level == 'MEDIUM':
        matched = [kw for kw in MEDIUM_KEYWORDS if kw in text]
        return f"Clasificado MEDIUM — keywords detectados: {matched}"
    else:
        return "Clasificado LOW — sin keywords de alerta detectados"


def find_correlations(db, agent: str, category: str) -> list:
    from core.database import ExecutivePriorityModel
    try:
        by_agent = db.query(ExecutivePriorityModel).filter(
            ExecutivePriorityModel.assigned_agent == agent,
            ExecutivePriorityModel.status == 'pending'
        ).limit(3).all()

        by_category = db.query(ExecutivePriorityModel).filter(
            ExecutivePriorityModel.category == category,
            ExecutivePriorityModel.status == 'pending'
        ).limit(3).all()

        seen = set()
        results = []
        for r in by_agent + by_category:
            if r.id not in seen:
                seen.add(r.id)
                results.append({
                    'id': r.id,
                    'title': r.title,
                    'priority_level': r.priority_level,
                    'match': 'agent' if r.assigned_agent == agent else 'category'
                })
        return results
    except Exception as e:
        print(f"[correlation] Error: {e}")
        return []

def process_report(db, report_id: str, agent: str, message: str, category: str):
    from core.database import ExecutivePriorityModel, TimelineModel

    try:
        level = classify_priority(agent, message, category)
        reasoning = build_reasoning(agent, message, category, level)

        priority = ExecutivePriorityModel(
            id=str(uuid.uuid4()),
            title=f"[{level}] {agent}: {message[:60]}",
            description=message[:200],
            category=category,
            priority_level=level,
            status='pending',
            assigned_agent=agent,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(priority)

        timeline = TimelineModel(
            id=str(uuid.uuid4()),
            event_type='priority_auto_classified',
            title=f"Prioridad {level} — {agent}",
            description=reasoning,
            importance=level,
            created_at=datetime.utcnow(),
        )
        db.add(timeline)
        db.commit()

        from core.telegram_gateway import notify_escalation
        notify_escalation(agent, message, level, reasoning)

        correlations = find_correlations(db, agent, category)
        if correlations:
            print(f'[correlation] {len(correlations)} correlaciones encontradas para {agent}/{category}')

        return level, reasoning, correlations

    except Exception as e:
        db.rollback()
        print(f"[priority_engine] Error: {e}")
        return 'LOW', f"Error en clasificacion: {e}"