import os
import uuid
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.database import SessionLocal, TelegramMessageModel, ReportModel, GoalModel, PriorityModel, ExecutivePriorityModel, DecisionMemoryModel, TimelineModel

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8668242201:AAENQTquDPzLwGFvCsKGYhHbIucXWIv-CdU')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '7859486600')

def save_message(sender, message, direction):
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
        print(f'Error saving message: {e}')
    finally:
        db.close()

def is_authorized(chat_id):
    return str(chat_id) == str(TELEGRAM_CHAT_ID)

async def cmd_status(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/status', 'incoming')
    db = SessionLocal()
    try:
        reports = db.query(ReportModel).count()
        goals = db.query(GoalModel).filter(GoalModel.status == 'ACTIVE').count()
        exec_priorities = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.status == 'pending').count()
        critical = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.priority_level == 'CRITICAL', ExecutivePriorityModel.status == 'pending').count()
        text = '🧠 <b>CEREBRO STATUS</b>

📋 Reportes totales: ' + str(reports) + '
🎯 Metas activas: ' + str(goals) + '
⚡ Prioridades ejecutivas pendientes: ' + str(exec_priorities) + '
🚨 Criticas sin resolver: ' + str(critical) + '

✅ Sistema operacional'
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def cmd_reportes(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/reportes', 'incoming')
    db = SessionLocal()
    try:
        records = db.query(ReportModel).order_by(ReportModel.created_at.desc()).limit(5).all()
        if not records:
            text = '📋 No hay reportes aun.'
        else:
            lines = ['📋 <b>ULTIMOS REPORTES</b>
']
            for r in records:
                lines.append('- <b>' + r.agent + '</b> [' + r.priority + '] -- ' + r.message[:80])
            text = '
'.join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def cmd_metas(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/metas', 'incoming')
    db = SessionLocal()
    try:
        records = db.query(GoalModel).filter(GoalModel.status == 'ACTIVE').limit(5).all()
        if not records:
            text = '🎯 No hay metas activas.'
        else:
            lines = ['🎯 <b>METAS ACTIVAS</b>
']
            for r in records:
                lines.append('- ' + r.title)
            text = '
'.join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def cmd_prioridades(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/prioridades', 'incoming')
    db = SessionLocal()
    try:
        records = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.status == 'pending').order_by(ExecutivePriorityModel.created_at.desc()).limit(5).all()
        if not records:
            text = '⚡ No hay prioridades ejecutivas pendientes.'
        else:
            lines = ['⚡ <b>PRIORIDADES EJECUTIVAS PENDIENTES</b>
']
            for r in records:
                emoji = '🚨' if r.priority_level == 'CRITICAL' else '🔴' if r.priority_level == 'HIGH' else '🟡'
                lines.append(emoji + ' <b>' + r.title + '</b> [' + r.priority_level + ']
   ' + (r.description[:80] if r.description else ''))
            text = '
'.join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def cmd_decisions(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/decisions', 'incoming')
    db = SessionLocal()
    try:
        records = db.query(DecisionMemoryModel).order_by(DecisionMemoryModel.created_at.desc()).limit(5).all()
        if not records:
            text = '🧠 No hay decisiones registradas.'
        else:
            lines = ['🧠 <b>ULTIMAS DECISIONES</b>
']
            for r in records:
                lines.append('- <b>' + r.topic + '</b>
   ' + r.decision[:100])
            text = '
'.join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def cmd_timeline(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/timeline', 'incoming')
    db = SessionLocal()
    try:
        records = db.query(TimelineModel).order_by(TimelineModel.created_at.desc()).limit(7).all()
        if not records:
            text = '📅 No hay eventos en el timeline.'
        else:
            lines = ['📅 <b>TIMELINE RECIENTE</b>
']
            for r in records:
                emoji = '🚨' if r.importance == 'CRITICAL' else '🔴' if r.importance == 'HIGH' else '📌'
                fecha = r.created_at.strftime('%d/%m %H:%M')
                lines.append(emoji + ' <b>' + r.title + '</b> [' + fecha + ']
   ' + (r.description[:80] if r.description else ''))
            text = '
'.join(lines)
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def cmd_resumen(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    save_message(str(update.effective_chat.id), '/resumen', 'incoming')
    db = SessionLocal()
    try:
        reports = db.query(ReportModel).count()
        goals_active = db.query(GoalModel).filter(GoalModel.status == 'ACTIVE').count()
        goals_done = db.query(GoalModel).filter(GoalModel.status == 'COMPLETED').count()
        exec_pending = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.status == 'pending').count()
        critical = db.query(ExecutivePriorityModel).filter(ExecutivePriorityModel.priority_level == 'CRITICAL', ExecutivePriorityModel.status == 'pending').count()
        decisions = db.query(DecisionMemoryModel).count()
        last_report = db.query(ReportModel).order_by(ReportModel.created_at.desc()).first()
        last_text = last_report.agent + ': ' + last_report.message[:60] if last_report else 'Sin reportes'
        text = '🧠 <b>RESUMEN EJECUTIVO CEREBRO</b>

📋 Reportes: ' + str(reports) + '
🎯 Metas activas: ' + str(goals_active) + ' | Completadas: ' + str(goals_done) + '
⚡ Prioridades ejecutivas pendientes: ' + str(exec_pending) + '
🚨 Criticas: ' + str(critical) + '
🧠 Decisiones registradas: ' + str(decisions) + '

📌 Ultimo reporte:
' + last_text
    finally:
        db.close()
    await update.message.reply_text(text, parse_mode='HTML')
    save_message('CEREBRO', text, 'outgoing')

async def handle_message(update, context):
    if not is_authorized(update.effective_chat.id):
        return
    text = update.message.text
    save_message(str(update.effective_chat.id), text, 'incoming')
    from core.response_engine import process_ceo_message
    await update.message.chat.send_action('typing')
    response = await process_ceo_message(text)
    await update.message.reply_text(response, parse_mode='HTML')
    save_message('CEREBRO', response, 'outgoing')

def build_app():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', cmd_status))
    application.add_handler(CommandHandler('status', cmd_status))
    application.add_handler(CommandHandler('resumen', cmd_resumen))
    application.add_handler(CommandHandler('reportes', cmd_reportes))
    application.add_handler(CommandHandler('metas', cmd_metas))
    application.add_handler(CommandHandler('prioridades', cmd_prioridades))
    application.add_handler(CommandHandler('priorities', cmd_prioridades))
    application.add_handler(CommandHandler('decisions', cmd_decisions))
    application.add_handler(CommandHandler('timeline', cmd_timeline))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application
