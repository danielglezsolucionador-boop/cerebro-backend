import os
import json
from core.context_engine import get_operational_context, get_conversation_history, save_conversation, save_ceo_memory, save_timeline_event

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """Eres CEREBRO — el Chief of Staff IA del ecosistema de Daniel González.

Tu rol es ser el brazo derecho operacional del CEO. No eres un bot. No eres un asistente genérico. Eres una entidad operacional que conoce el estado real de la empresa.

PRINCIPIOS:
- Responde basándote EXCLUSIVAMENTE en el contexto operacional real que se te proporciona
- Si no hay datos reales, dilo claramente: "No tengo datos sobre eso aún"
- Sé directo, estratégico, útil. Sin frases vacías
- Puedes contradecir al CEO si hay razones operacionales reales
- Detecta humo: si algo suena a marketing sin sustancia, dilo
- Prioriza: no todo es urgente, ayuda a filtrar
- Mantén continuidad conversacional usando el historial

FORMATO:
- Respuestas concisas y accionables
- Usa datos reales del contexto
- Cuando hay riesgos, nómbralos
- Cuando hay oportunidades, señálalas
- Sin emoji excesivo
- Sin tono corporativo robótico

NUNCA:
- Inventes datos
- Digas "Entendido CEO" sin aportar valor
- Repitas el contexto sin procesar
- Seas genérico
"""

async def build_claude_response(user_message: str) -> str:
    if not CLAUDE_API_KEY:
        return _fallback_response(user_message)
    
    try:
        import httpx
        
        context = get_operational_context()
        history = get_conversation_history(limit=10)
        
        context_text = f"""
CONTEXTO OPERACIONAL REAL — {context.get('timestamp', '')}

REPORTES ÚLTIMAS 24H: {json.dumps(context.get('reports', {}).get('recent_24h', []), ensure_ascii=False)}
REPORTES CRÍTICOS: {json.dumps(context.get('reports', {}).get('critical', []), ensure_ascii=False)}
METAS ACTIVAS: {json.dumps(context.get('goals', {}).get('active', []), ensure_ascii=False)}
PRIORIDADES PENDIENTES: {json.dumps(context.get('priorities', {}).get('pending', []), ensure_ascii=False)}
MEMORIA EJECUTIVA: {json.dumps(context.get('executive_memory', []), ensure_ascii=False)}
MEMORIA CEO: {json.dumps(context.get('ceo_memory', []), ensure_ascii=False)}
TIMELINE RECIENTE: {json.dumps(context.get('timeline', []), ensure_ascii=False)}
TOTALES: Reportes={context.get('reports', {}).get('total', 0)} | Metas={context.get('goals', {}).get('total', 0)} | Completadas={context.get('goals', {}).get('completed', 0)}
"""
        
        messages = []
        for h in history[-8:]:
            role = "user" if h["role"] == "ceo" else "assistant"
            messages.append({"role": role, "content": h["message"]})
        
        messages.append({"role": "user", "content": f"{context_text}\n\nMENSAJE CEO: {user_message}"})
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 1000,
                    "system": SYSTEM_PROMPT,
                    "messages": messages,
                },
            )
            data = response.json()
            return data["content"][0]["text"]
    
    except Exception as e:
        print(f"Claude API error: {e}")
        return _fallback_response(user_message)

def _fallback_response(user_message: str) -> str:
    context = get_operational_context()
    reports_24h = len(context.get("reports", {}).get("recent_24h", []))
    critical = len(context.get("reports", {}).get("critical", []))
    active_goals = len(context.get("goals", {}).get("active", []))
    priorities = context.get("priorities", {}).get("pending", [])
    pending_count = len(priorities)
    timeline = context.get("timeline", [])

    msg = user_message.lower()

    if any(w in msg for w in ["qué pasó", "que paso", "hoy", "resumen", "status", "estado", "cómo vamos", "como vamos"]):
        resumen = f"Hoy tenemos {reports_24h} reportes"
        resumen += f", {critical} críticos" if critical > 0 else ", sin críticos"
        resumen += f". {active_goals} metas activas"
        resumen += f". {pending_count} prioridades pendientes"
        if critical > 0:
            resumen += ". ⚠️ Hay críticos sin resolver — revisa /prioridades"
        elif pending_count == 0:
            resumen += ". Todo despejado por ahora."
        else:
            resumen += ". Operando normal."
        return resumen

    if any(w in msg for w in ["urgente", "crítico", "critico", "problema", "riesgo", "falla", "error"]):
        critical_items = [p for p in priorities if p.get("priority_level") in ("CRITICAL", "HIGH")]
        if critical_items:
            lines = [f"Hay {len(critical_items)} prioridades HIGH/CRITICAL abiertas:"]
            for p in critical_items[:3]:
                lines.append(f"• [{p.get('priority_level')}] {p.get('title', '')[:60]}")
            return "\n".join(lines)
        return "Sin críticos activos en este momento. Sistema estable."

    if any(w in msg for w in ["meta", "objetivo", "goal", "metas"]):
        if active_goals == 0:
            return "No hay metas activas registradas. ¿Quieres crear una?"
        return f"Tienes {active_goals} metas activas. Usa /metas para el detalle completo."

    if any(w in msg for w in ["prioridad", "priorit", "pendiente"]):
        if pending_count == 0:
            return "No hay prioridades pendientes. Todo resuelto."
        lines = [f"Hay {pending_count} prioridades pendientes:"]
        for p in priorities[:3]:
            lines.append(f"• [{p.get('priority_level')}] {p.get('title', '')[:60]}")
        return "\n".join(lines)

    if any(w in msg for w in ["semana", "week", "resumen semanal"]):
        total = context.get("reports", {}).get("total", 0)
        completed = context.get("goals", {}).get("completed", 0)
        return f"Esta semana: {total} reportes totales, {completed} metas completadas, {pending_count} prioridades abiertas. {'Hay críticos sin resolver.' if critical > 0 else 'Sin alertas críticas.'}"

    if any(w in msg for w in ["agente", "agent", "quién", "quien"]):
        recent = context.get("reports", {}).get("recent_24h", [])
        if recent:
            agentes = list(set(r.get("agent", "") for r in recent[:10]))
            return f"Agentes activos hoy: {', '.join(agentes[:5])}."
        return "No hay actividad de agentes en las últimas 24h."

    if any(w in msg for w in ["timeline", "eventos", "historial"]):
        if not timeline:
            return "No hay eventos recientes en el timeline."
        lines = ["Últimos eventos:"]
        for t in timeline[:4]:
            lines.append(f"• {t.get('title', '')[:60]}")
        return "\n".join(lines)

    return f"Contexto activo: {reports_24h} reportes hoy, {active_goals} metas, {pending_count} prioridades. ¿Qué necesitas revisar?"


async def process_ceo_message(user_message: str) -> str:
    save_conversation("ceo", user_message, "operational")
    response = await build_claude_response(user_message)
    save_conversation("cerebro", response, "operational")
    
    _detect_ceo_patterns(user_message)
    
    return response

def _detect_ceo_patterns(message: str):
    msg = message.lower()
    if any(w in msg for w in ["prioridad", "primero", "urgente", "focus"]):
        save_ceo_memory("prioridad", f"CEO mencionó: {message[:100]}", "conversation")
    if any(w in msg for w in ["no", "cancelar", "parar", "rechazar"]):
        save_ceo_memory("rechazo", f"CEO rechazó: {message[:100]}", "conversation")
    if any(w in msg for w in ["aprobado", "adelante", "sí", "hazlo"]):
        save_ceo_memory("aprobacion", f"CEO aprobó: {message[:100]}", "conversation")
    if any(w in msg for w in ["humo", "fake", "marketing", "exagerado"]):
        save_ceo_memory("antihumo", f"CEO marcó como humo: {message[:100]}", "conversation")