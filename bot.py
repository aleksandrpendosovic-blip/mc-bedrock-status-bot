import os
import asyncio
from mcstatus import BedrockServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔧 ПЕРЕМЕННЫЕ ИЗ RAILWAY
TOKEN = os.getenv("TOKEN")
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = int(os.getenv("SERVER_PORT", 19132))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

UPDATE_INTERVAL = 300  # 5 минут
CHECKS = 3             # проверок подряд

status_message_id = None
chat_id = None


def check_server():
    success = 0
    latency = None
    online = None
    maxp = None

    for _ in range(CHECKS):
        try:
            server = BedrockServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
            status = server.status()
            success += 1
            latency = round(status.latency)
            online = status.players_online
            maxp = status.players_max
        except:
            pass

    if success == CHECKS:
        return "ONLINE", latency, online, maxp
    elif success > 0:
        return "STARTING", None, None, None
    else:
        return "OFFLINE", None, None, None


def get_status_text():
    state, latency, online, maxp = check_server()

    if state == "ONLINE":
        return (
            "🟢 *BEDROCK СЕРВЕР ONLINE*\n\n"
            f"👥 Онлайн: {online}/{maxp}\n"
            f"📡 Пинг: {latency} ms"
        )

    if state == "STARTING":
        return (
            "🟡 *BEDROCK СЕРВЕР ЗАПУСКАЕТСЯ*\n\n"
            "⏳ Сервер включается, подожди..."
        )

    return (
        "🔴 *BEDROCK СЕРВЕР OFFLINE*\n\n"
        "⛔ Сервер выключен"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global status_message_id, chat_id

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Команда только для администратора")
        return

    chat_id = update.effective_chat.id
    msg = await update.message.reply_text(
        get_status_text(),
        parse_mode="Markdown"
    )
    status_message_id = msg.message_id

    await update.message.reply_text("✅ Статус создан, закрепи сообщение 📌")


async def auto_update(app):
    global status_message_id, chat_id

    while True:
        if status_message_id and chat_id:
            try:
                await app.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text=get_status_text(),
                    parse_mode="Markdown"
                )
            except:
                pass

        await asyncio.sleep(UPDATE_INTERVAL)


async def on_startup(app):
    app.create_task(auto_update(app))


app = (
    ApplicationBuilder()
    .token(TOKEN)
    .post_init(on_startup)
    .build()
)

app.add_handler(CommandHandler("start", start))

print("Бот запущен...")
app.run_polling()
