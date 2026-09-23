import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Импорт бэкенд-модулей Du&Yes
from database import init_db, get_user, create_user
from search import search_callback
from chat import start_chat
from translations import t

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("DuYesApp")

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://duyes-app.onrender.com
PORT = int(os.getenv("PORT", 8080))

# Поддерживаемые языки
SUPPORTED_LANGUAGES = ("ru", "hy", "en", "fr")

# Инициализация приложения python-telegram-bot
ptb_app = Application.builder().token(BOT_TOKEN).build()


# ============================================================
# ОБРАБОТЧИКИ ТЕЛЕГРАМ-БОТА
# ============================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Приветственная команда /start с автоопределением языка и мультиязычным выводом.
    """
    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        # Определяем язык из настроек Telegram пользователя (например, 'ru-RU' -> 'ru')
        telegram_lang = (update.effective_user.language_code or "ru").split("-")[0].lower()
        language = telegram_lang if telegram_lang in SUPPORTED_LANGUAGES else "ru"

        create_user(
            user_id=user_id,
            language=language,
        )
        lang = language
    else:
        lang = user.get("language", "ru")

    # Формируем приветствие полностью на языке пользователя из translations.py
    welcome_header = t(lang, "welcome")
    trial_info = t(lang, "trial_active")

    if trial_info:
        welcome_text = f"{welcome_header}\n\n{trial_info}"
    else:
        welcome_text = welcome_header

    await update.message.reply_text(welcome_text)


def register_bot_handlers(app: Application):
    """
    Регистрация всех хэндлеров бота.
    """
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(search_callback))


# ============================================================
# FASTAPI СЕРВЕР & WEBHOOK LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом: инициализация БД и жизненный цикл бота.
    """
    init_db()
    register_bot_handlers(ptb_app)

    await ptb_app.initialize()
    await ptb_app.start()

    # Если задан WEBHOOK_URL (для деплоя на Render), регистрируем вебхук
    if WEBHOOK_URL:
        webhook_endpoint = f"{WEBHOOK_URL.rstrip('/')}/webhook"
        logger.info(f"Setting webhook URL to: {webhook_endpoint}")
        await ptb_app.bot.set_webhook(url=webhook_endpoint)
    else:
        logger.info("WEBHOOK_URL unset. Webhook setup skipped.")

    yield

    # Корректная остановка вебхука и приложения
    if WEBHOOK_URL:
        await ptb_app.bot.delete_webhook()
    await ptb_app.stop()
    await ptb_app.shutdown()


app = FastAPI(title="Du&Yes Service Engine", lifespan=lifespan)

# Монтирование статики Telegram Mini App (HTML/JS/CSS)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Выдача интерфейса Mini App.
    """
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Du&Yes App Server Running</h1>")


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Эндпоинт приёма вебхуков от Telegram API.
    """
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return JSONResponse(content={"status": "ok"})


@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса для хостинга Render.
    """
    return {"status": "healthy", "service": "Du&Yes"}


# ============================================================
# ЗАПУСК СЕРВЕРА
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
