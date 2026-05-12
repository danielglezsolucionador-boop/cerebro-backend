import os
import uuid
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.database import SessionLocal, TelegramMessageModel, ReportModel, GoalModel, PriorityModel

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8668242201:AAENQTquDPzLwGFvCsKGYhHbIucXWIv-CdU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7859486600")

def save_message(sender: str, message: str, direction: str):
    db = SessionLocal()
    try:
        record = TelegramMessageModel(
            id=str(uuid.uuid4()),
            sender=sender,
            message=message,
            direction=direction,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving message: {e}")
    finally:
        db.close()

def is_authorized(chat_id: int) -> bool:
    return str(chat_id) == str(TELEGRAM_CHAT_ID)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), "/status", "incoming")
    db = SessionLocal()
    try:
        reports = db.query(ReportModel).count()
        goals = db.query(GoalModel).filter(GoalModel.status == "ACTIVE").count()
        priorities = db.query(PriorityModel).filter(PriorityModel.resolved == False).count()
        text = f"🧠 <b>CEREBRO STATUS</b>\n\n📋 Reportes totales: {reports}\n🎯 Metas activas: {goals}\n⚡ Prioridades pendientes: {priorities}\n\n✅ Sistema operacional"
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode="HTML")
    save_message("CEREBRO", text, "outgoing")

async def cmd_reportes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), "/reportes", "incoming")
    db = SessionLocal()
    try:
        records = db.query(ReportModel).order_by(ReportModel.created_at.desc()).limit(5).all()
        if not records:
            text = "📋 No hay reportes aún."
        else:
            lines = ["📋 <b>ÚLTIMOS REPORTES</b>\n"]
            for r in records:
                lines.append(f"• <b>{r.agent}</b> [{r.priority}] — {r.message[:80]}")
            text = "\n".join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode="HTML")
    save_message("CEREBRO", text, "outgoing")

async def cmd_metas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), "/metas", "incoming")
    db = SessionLocal()
    try:
        records = db.query(GoalModel).filter(GoalModel.status == "ACTIVE").limit(5).all()
        if not records:
            text = "🎯 No hay metas activas."
        else:
            lines = ["🎯 <b>METAS ACTIVAS</b>\n"]
            for r in records:
                lines.append(f"• {r.title} [{r.priority}]")
            text = "\n".join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode="HTML")
    save_message("CEREBRO", text, "outgoing")

async def cmd_prioridades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), "/prioridades", "incoming")
    db = SessionLocal()
    try:
        records = db.query(PriorityModel).filter(PriorityModel.resolved == False).limit(5).all()
        if not records:
            text = "⚡ No hay prioridades pendientes."
        else:
            lines = ["⚡ <b>PRIORIDADES PENDIENTES</b>\n"]
            for r in records:
                lines.append(f"• [{r.level}] {r.reason[:80]}")
            text = "\n".join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode="HTML")
    save_message("CEREBRO", text, "outgoing")

async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), "/resumen", "incoming")
    db = SessionLocal()
    try:
        reports = db.query(ReportModel).count()
        goals_active = db.query(GoalModel).filter(GoalModel.status == "ACTIVE").count()
        goals_done = db.query(GoalModel).filter(GoalModel.status == "COMPLETED").count()
        priorities = db.query(PriorityModel).filter(PriorityModel.resolved == False).count()
        last_report = db.query(ReportModel).order_by(ReportModel.created_at.desc()).first()
        last_text = f"{last_report.agent}: {last_report.message[:60]}" if last_report else "Sin reportes"
        text = f"🧠 <b>RESUMEN EJECUTIVO CEREBRO</b>\n\n📋 Reportes: {reports}\n🎯 Metas activas: {goals_active} | Completadas: {goals_done}\n⚡ Prioridades pendientes: {priorities}\n\n📌 Último reporte:\n{last_text}"
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode="HTML")
    save_message("CEREBRO", text, "outgoing")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        return
    text = update.message.text
    save_message(str(update.effective_chat.id), text, "incoming")
    response = "🧠 CEREBRO recibió tu mensaje. Usa /status /resumen /reportes /metas /prioridades"
    await update.message.reply_text(response, parse_mode="HTML")
    save_message("CEREBRO", response, "outgoing")

def build_app():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_status))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("resumen", cmd_resumen))
    application.add_handler(CommandHandler("reportes", cmd_reportes))
    application.add_handler(CommandHandler("metas", cmd_metas))
    application.add_handler(CommandHandler("prioridades", cmd_prioridades))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application