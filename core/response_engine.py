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
    priorities = len(context.get("priorities", {}).get("pending", []))
    
    msg = user_message.lower()
    
    if any(w in msg for w in ["qué pasó", "que paso", "hoy", "status", "estado"]):
        return f"Hoy: {reports_24h} reportes recibidos, {critical} críticos. {active_goals} metas activas. {priorities} prioridades pendientes. [Claude API pendiente de activación]"
    
    if any(w in msg for w in ["problema", "riesgo", "falla", "error"]):
        if critical > 0:
            return f"Hay {critical} reportes críticos activos. Revisa /reportes para detalle. [Claude API pendiente]"
        return "No hay reportes críticos activos en este momento. [Claude API pendiente]"
    
    if any(w in msg for w in ["meta", "objetivo", "goal"]):
        return f"Tienes {active_goals} metas activas. Usa /metas para detalle. [Claude API pendiente]"
    
    if any(w in msg for w in ["prioridad", "urgente", "priorit"]):
        return f"Hay {priorities} prioridades pendientes. Usa /prioridades para detalle. [Claude API pendiente]"
    
    return f"Contexto cargado: {reports_24h} reportes, {active_goals} metas, {priorities} prioridades. Claude API pendiente de activación para respuestas inteligentes."

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