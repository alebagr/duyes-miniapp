from datetime import date, datetime
import os
from fastapi import APIRouter, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Импортируем ваши существующие бизнес-модули проекта
from database import (
    add_favorite,
    add_message,
    add_report,
    block_user,
    get_conversations,
    get_messages,
    is_messages_blocked,
    is_permanently_blocked,
    remove_favorite,
)
from moderation import moderate_message
from photo_compare import check_registration_photos
from search import build_location_text, calculate_age, prepare_search
from translations import TRANSLATIONS

app = FastAPI(title="Du&Yes Mini App Backend")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы фронтенда (если папка static существует)
if os.path.exists("static"):
    app.mount("/app", StaticFiles(directory="static", html=True), name="static")


# --- УТИЛИТА ПРОВЕРКИ ВОЗРАСТА (18 - 72 лет) ---
def validate_user_age(birth_date_str: str) -> int | None:
  try:
    if "-" in birth_date_str:
      birth = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    else:
      birth = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
  except (TypeError, ValueError):
    return None

  today = date.today()
  age = (
      today.year
      - birth.year
      - ((today.month, today.day) < (birth.month, birth.day))
  )

  if 18 <= age <= 72:
    return age
  return None


# --- 1. ЭНДПОИНТЫ РЕГИСТРАЦИИ ---


@app.post("/api/register")
async def register_user_endpoint(
    gender: str = Form(...),
    first_name: str = Form(...),
    birth_date: str = Form(...),
    country_code: str = Form(...),
    country: str = Form(...),
    city: str = Form(...),
    married: str = Form(...),
    children: str = Form(...),
    about: str = Form(...),
    photo_1: UploadFile = File(...),
    photo_2: UploadFile = File(...),
    x_telegram_init_data: str = Header(None),
):
  # Строгая проверка возраста (18–72 года)
  age = validate_user_age(birth_date)
  if not age:
    raise HTTPException(
        status_code=400,
        detail="Регистрация возможна только для пользователей от 18 до 72 лет.",
    )

  # Чтение байтов фотографий
  p1_bytes = await photo_1.read()
  p2_bytes = await photo_2.read()

  user_id = 1001  # Заглушка/получение ID из initData

  # Проверка фото через ваш модуль photo_compare.py
  try:
    photo_check = check_registration_photos(user_id, p1_bytes, p2_bytes)
  except Exception as e:
    raise HTTPException(
        status_code=400, detail=f"Ошибка проверки фотографий: {str(e)}"
    )

  if photo_check and photo_check.get("status") == "rejected":
    reason = photo_check.get(
        "reason", "Фото не соответствуют правилам сервиса."
    )
    raise HTTPException(
        status_code=400, detail=f"Фотография отклонена: {reason}"
    )

  return {
      "status": "success",
      "message": "Регистрация успешно завершена!",
  }


# --- 2. ЭНДПОИНТЫ ПОИСКА И ЛЕНТЫ (search.py) ---


class ActionRequest(BaseModel):
  target_user_id: int
  action: str  # "favorite", "remove_favorite", "block", "report"


@app.get("/api/search/feed")
async def get_search_feed(x_telegram_init_data: str = Header(None)):
  user_id = 1001
  profiles = prepare_search(user_id)

  formatted_profiles = []
  for p in profiles:
    formatted_profiles.append({
        "id": p.get("id"),
        "first_name": p.get("first_name"),
        "age": calculate_age(p.get("birth_date")),
        "location": build_location_text(p),  # Флаг + Страна/Город
        "about": p.get("about"),
        "photo": p.get("photo_1"),
    })

  return {"profiles": formatted_profiles}


@app.post("/api/search/action")
async def handle_profile_action(
    req: ActionRequest, x_telegram_init_data: str = Header(None)
):
  user_id = 1001

  if req.action == "favorite":
    add_favorite(user_id, req.target_user_id)
  elif req.action == "remove_favorite":
    remove_favorite(user_id, req.target_user_id)
  elif req.action == "block":
    block_user(user_id, req.target_user_id)
  elif req.action == "report":
    add_report(reporter_id=user_id, reported_id=req.target_user_id)
  else:
    raise HTTPException(status_code=400, detail="Invalid action")

  return {"status": "success", "action": req.action}


# --- 3. ЭНДПОИНТЫ ЧАТА И МОДЕРАЦИИ ---


@app.get("/api/chats")
async def get_user_chats(x_telegram_init_data: str = Header(None)):
  user_id = 1001
  conversations = get_conversations(user_id)
  return {"conversations": conversations}


@app.get("/api/chats/{receiver_id}/messages")
async def get_chat_messages(
    receiver_id: int, x_telegram_init_data: str = Header(None)
):
  user_id = 1001
  messages = get_messages(user_id, receiver_id)
  return {"messages": messages}


class SendMessageRequest(BaseModel):
  receiver_id: int
  text: str


@app.post("/api/chats/send")
async def send_chat_message(
    req: SendMessageRequest, x_telegram_init_data: str = Header(None)
):
  user_id = 1001

  # Проверка модерации текста сообщения
  if not moderate_message(user_id, req.text):
    if is_permanently_blocked(user_id):
      raise HTTPException(
          status_code=403,
          detail=(
              "Аккаунт заблокирован перманентно за нарушение правил"
              " (реклама/услуги)."
          ),
      )
    if is_messages_blocked(user_id):
      raise HTTPException(
          status_code=403,
          detail="Отправка сообщений заблокирована на 3 дня.",
      )
    raise HTTPException(
        status_code=400, detail="Сообщение заблокировано правилами модерации."
    )

  # Добавление сообщения с учетом лимита (макс. 3 неотвеченных)
  message_id = add_message(
      sender_id=user_id,
      receiver_id=req.receiver_id,
      text=req.text,
      message_type="text",
  )

  if not message_id:
    raise HTTPException(
        status_code=400,
        detail=(
            "Не удалось отправить сообщение. Превышен лимит (максимум 3"
            " неотвеченных сообщения подряд)."
        ),
    )

  return {"status": "success", "message_id": message_id}


# --- ПЕРЕВОДЫ ---
@app.get("/api/translations/{lang}")
async def get_translations(lang: str):
  if lang not in TRANSLATIONS:
    lang = "ru"
  return TRANSLATIONS[lang]
