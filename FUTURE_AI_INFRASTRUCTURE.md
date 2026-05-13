mensaje CEO
→ clasificador de intención (modelo barato)
→ si operacional simple → Haiku
→ si estratégico → Sonnet
→ si análisis profundo → Opus
→ si imagen/PDF → GPT-4o
→ si falla proveedor → fallback automático

---

## CONTROL FINANCIERO

### Presupuesto mensual estimado (fase inicial)
- CEREBRO conversacional: ~$20-40/mes con Sonnet
- Con optimización por tarea: ~$8-15/mes
- Centinela (análisis prompts): $0 — no usa LLM en pipeline actual

### Métricas a implementar
- tokens consumidos por agente
- costo por conversación
- costo por reporte procesado
- ROI por agente (valor generado vs costo API)
- alertas cuando consumo supera umbral

### Límites por aplicación
- CEREBRO Telegram: 500 llamadas/día
- PLUMA editorial: 200 llamadas/día
- Centinela: sin LLM en pipeline (solo patrones)
- MCF financiero: 100 llamadas/día premium

---

## PROVEEDORES Y FALLBACK

### Proveedores activos futuros
1. Anthropic (Claude) — principal
2. OpenAI (GPT-4o, embeddings) — secundario
3. Google (Gemini) — multimodal especializado
4. Groq (Llama) — velocidad, costo mínimo

### Estrategia de fallback
- Si Anthropic falla → OpenAI automático
- Si OpenAI falla → Groq (respuesta básica)
- Si todos fallan → respuesta con datos PostgreSQL puros sin LLM

### Criterios de switching
- latencia > 5s → cambiar modelo
- error rate > 5% en 10 min → fallback
- costo diario > umbral → bajar a modelo más barato

---

## ADMINISTRACIÓN CENTRALIZADA

### Tabla futura: ai_usage_log
id, agent, model, tokens_in, tokens_out, cost_usd, task_type, created_at

### Tabla futura: ai_budget
id, agent, model, monthly_limit_usd, current_usage_usd, month, alert_threshold

### Endpoint futuro: GET /api/v1/ai/stats
- consumo total por agente
- costo acumulado mes
- modelo más usado
- alertas de presupuesto

---

## SEPARACIÓN OPERACIONAL VS ESTRATÉGICO

### Modo Operacional
- tareas diarias
- reportes
- status
- incidentes
- modelo: Haiku o Sonnet básico
- latencia objetivo: < 2s
- costo objetivo: mínimo

### Modo Estratégico
- análisis de decisiones
- evaluación de riesgos
- planificación
- modelo: Sonnet o Opus
- latencia aceptable: hasta 10s
- costo aceptable: premium justificado

---

## MULTIMODALIDAD FUTURA

### Voz
- Telegram envía audio → Whisper transcribe → CEREBRO procesa
- Proveedor: OpenAI Whisper ($0.006/min)
- Implementación: cuando volumen conversacional lo justifique

### Imágenes / Screenshots
- CEO envía screenshot → GPT-4o Vision analiza → CEREBRO responde
- Uso: análisis de dashboards, competencia, UI

### PDFs / Documentos
- CEO envía PDF → extracción texto → chunking → embedding → búsqueda semántica
- Proveedor: text-embedding-3-small + pgvector futuro

### Links / Web
- CEO envía URL → scraping → resumen → análisis antihumo
- Proveedor: Jina Reader o similar

---

## MEMORIA SEMÁNTICA FUTURA

### Problema actual
- memoria CEO guardada como texto plano
- búsqueda solo por fecha/categoría
- no hay búsqueda por similitud semántica

### Solución futura
- embeddings de cada memoria CEO
- pgvector en PostgreSQL
- búsqueda semántica: "qué decisiones tomé sobre PLUMA"
- recuperación contextual inteligente

### Costo estimado
- 10,000 memorias × 1,536 dims = mínimo
- $0.02 por cada 1M tokens de embedding
- prácticamente gratis a escala inicial

---

## RIESGOS PREVISIBLES

1. **Vendor lock-in Anthropic** — mitigar con abstracción de proveedor desde ahora
2. **Costos escalando sin control** — mitigar con límites por agente y alertas
3. **Latencia variable** — mitigar con timeout agresivo y fallback
4. **Calidad degradada en modelo barato** — mitigar con clasificador de complejidad
5. **API key comprometida** — mitigar con rotación periódica y permisos mínimos
6. **Cambios de pricing proveedores** — monitoreo mensual y switching dinámico

---

## VENTAJAS DE ESTA ARQUITECTURA

- costo optimizado por tipo de tarea
- resiliencia ante fallos de proveedor
- visibilidad financiera real
- escalable sin reescribir arquitectura
- cada agente del ecosistema controlado independientemente
- auditoría completa de consumo IA

---

## ESCALABILIDAD

### Fase actual (MVP)
- 1 modelo, 1 proveedor, sin métricas
- costo: $20-40/mes estimado

### Fase 2 (cuando haya volumen real)
- routing por tipo de tarea
- métricas básicas de consumo
- costo: $10-20/mes optimizado

### Fase 3 (ecosistema completo)
- múltiples agentes con presupuesto individual
- memoria semántica con embeddings
- multimodalidad completa
- costo: $50-100/mes con 10+ agentes activos

---

## IMPLEMENTACIÓN RECOMENDADA

Orden de prioridad cuando llegue el momento:

1. ai_usage_log tabla + logging básico
2. presupuesto por agente con alertas
3. routing Haiku vs Sonnet por complejidad
4. fallback OpenAI si Anthropic falla
5. Whisper para voz en Telegram
6. pgvector para memoria semántica
7. multimodalidad imágenes/PDFs

---

## NOTA FINAL

Este documento es arquitectura real basada en el ecosistema actual.
No es aspiracional. Es el mapa de lo que viene cuando el volumen lo justifique.
Actualizar cada vez que se tome una decisión arquitectural sobre IA.