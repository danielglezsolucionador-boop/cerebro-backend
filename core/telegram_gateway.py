import asyncio
from telegram import Bot
from telegram.error import TelegramError
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8668242201:AAENQTquDPzLwGFvCsKGYhHbIucXWIv-CdU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7859486600")

bot = Bot(token=TELEGRAM_TOKEN)

async def send_message(text: str, parse_mode: str = "HTML"):
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=parse_mode,
        )
        return True
    except TelegramError as e:
        print(f"Telegram error: {e}")
        return False

def notify(text: str):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(send_message(text))
        else:
            loop.run_until_complete(send_message(text))
    except Exception as e:
        print(f"Notify error: {e}")

def notify_report(agent: str, message: str, priority: str = "NORMAL"):
    emoji = "🚨" if priority == "CRITICAL" else "⚠️" if priority == "HIGH" else "📋"
    text = f"{emoji} <b>REPORTE CEREBRO</b>\n\n<b>Agente:</b> {agent}\n<b>Prioridad:</b> {priority}\n\n{message}"
    notify(text)

def notify_goal(title: str, status: str):
    emoji = "✅" if status == "COMPLETED" else "🎯"
    text = f"{emoji} <b>OBJETIVO ACTUALIZADO</b>\n\n<b>Título:</b> {title}\n<b>Estado:</b> {status}"
    notify(text)

def notify_alert(message: str):
    text = f"🔴 <b>ALERTA CEREBRO</b>\n\n{message}"
    notify(text)
def notify_escalation(agent: str, message: str, level: str, reasoning: str):
    if level not in ('HIGH', 'CRITICAL'):
        return
    emoji = '🚨' if level == 'CRITICAL' else '🔴'
    text = (
        f"{emoji} <b>ESCALAMIENTO {level}</b>\n\n"
        f"<b>Agente:</b> {agent}\n"
        f"<b>Nivel:</b> {level}\n"
        f"<b>Mensaje:</b> {message[:100]}\n\n"
        f"<b>Razon:</b> {reasoning}"
    )
    notify(text)
