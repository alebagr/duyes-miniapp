import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR
DB_NAME = os.getenv("DB_NAME", "duyes.db")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
INIT_DATA_MAX_AGE = int(os.getenv("MINIAPP_INIT_DATA_MAX_AGE", "86400"))

app = FastAPI(title="Du&Yes Mini App API", version="2.0.0")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def send_telegram_notification(user_id: int, text: str):
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": user_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending TG notification to {user_id}: {e}")


def validate_init_data(init_data: str):
    if not BOT_TOKEN:
        raise HTTPException(500, "BOT_TOKEN is not configured")
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop("hash", None)
        if not received_hash:
            raise ValueError("hash missing")
        auth_date = int(pairs.get("auth_date", "0"))
        if not auth_date or time.time() - auth_date > INIT_DATA_MAX_AGE:
            raise ValueError("init data expired")
        data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash):
            raise ValueError("invalid hash")
        user_raw = pairs.get("user")
        if not user_raw:
            raise ValueError("user missing")
        user = json.loads(user_raw)
        return int(user["id"])
    except (ValueError, KeyError, json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(401, f"Invalid Telegram initData: {exc}")


def current_user(x_telegram_init_data: str | None):
    if not x_telegram_init_data:
        raise HTTPException(401, "Telegram initData is required")
    return validate_init_data(x_telegram_init_data)


def calculate_age(birth_date):
    if not birth_date:
        return None
    try:
        b = date.fromisoformat(str(birth_date)[:10])
        today = date.today()
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    except ValueError:
        return None


@app.get("/api/health")
def health():
    return {"ok": True, "service": "duyes-miniapp"}


@app.get("/api/me")
def me(x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    
    # Получение баланса монет
    bal_row = conn.execute("SELECT coins FROM gift_balances WHERE user_id=?", (uid,)).fetchone()
    coins = bal_row["coins"] if bal_row else 0
    conn.close()

    if not row:
        return {"registered": False, "user_id": uid, "coins": coins}
    
    data = dict(row)
    data["age"] = calculate_age(data.get("birth_date"))
    data["verification_status"] = data.get("verification_status", "none")
    data["coins"] = coins
    return {"registered": True, "user": data}


@app.post("/api/me")
def update_profile(data: dict, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    
    conn.execute("""
        INSERT INTO users (user_id, name, gender, birth_date, country, city, about, profile_published)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            gender = excluded.gender,
            birth_date = excluded.birth_date,
            country = excluded.country,
            city = excluded.city,
            about = excluded.about,
            profile_published = 1,
            updated_at = CURRENT_TIMESTAMP
    """, (
        uid,
        data.get("name"),
        data.get("gender", "male"),
        data.get("birth_date"),
        data.get("country"),
        data.get("city"),
        data.get("about")
    ))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/profiles")
def profiles(
    x_telegram_init_data: str | None = Header(default=None),
    country: str | None = None,
    city: str | None = None,
    min_age: int | None = Query(default=None, ge=18, le=100),
    max_age: int | None = Query(default=None, ge=18, le=100),
):
    uid = current_user(x_telegram_init_data)
    conn = db()
    me_row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    
    gender_filter = ""
    params = [uid]
    if me_row and me_row["gender"]:
        opposite = "female" if str(me_row["gender"]).lower() in {"male", "мужчина", "м"} else "male"
        gender_filter = "AND gender=?"
        params.append(opposite)

    rows = conn.execute(
        f"SELECT * FROM users WHERE profile_published=1 AND profile_blocked=0 AND user_id<>? {gender_filter}",
        params
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        p = dict(row)
        age = calculate_age(p.get("birth_date"))
        if min_age is not None and (age is None or age < min_age):
            continue
        if max_age is not None and (age is None or age > max_age):
            continue
        if country and p.get("country") != country:
            continue
        if city and p.get("city") != city:
            continue
        result.append({
            "user_id": p.get("user_id"),
            "name": p.get("name"),
            "age": age,
            "country": p.get("country"),
            "city": p.get("city"),
            "about": p.get("about"),
            "photo_1_file_id": p.get("photo_1_file_id"),
            "verified": p.get("verification_status") == "verified",
        })
    return {"profiles": result}


@app.get("/api/chats")
def chats(x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    rows = conn.execute("""
        SELECT DISTINCT 
            CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as peer_id
        FROM messages 
        WHERE sender_id = ? OR receiver_id = ?
    """, (uid, uid, uid)).fetchall()

    peers = []
    for r in rows:
        peer_id = r["peer_id"]
        u = conn.execute("SELECT name, city, photo_1_file_id, verification_status FROM users WHERE user_id=?", (peer_id,)).fetchone()
        last_msg = conn.execute("""
            SELECT text, created_at FROM messages 
            WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
            ORDER BY message_id DESC LIMIT 1
        """, (uid, peer_id, peer_id, uid)).fetchone()

        if u:
            peers.append({
                "user_id": peer_id,
                "name": u["name"] or "Пользователь",
                "city": u["city"],
                "verified": u["verification_status"] == "verified",
                "last_message": last_msg["text"] if last_msg else "",
                "time": last_msg["created_at"] if last_msg else ""
            })
    conn.close()
    return {"chats": peers}


@app.get("/api/messages/{peer_id}")
def messages(peer_id: int, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    rows = conn.execute("""
        SELECT * FROM messages 
        WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
        ORDER BY message_id ASC
    """, (uid, peer_id, peer_id, uid)).fetchall()
    conn.close()
    return {"messages": [dict(r) for r in rows]}


@app.post("/api/messages/send")
def send_message(data: dict, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    receiver_id = data.get("receiver_id")
    text = data.get("text", "").strip()

    if not receiver_id or not text:
        raise HTTPException(400, "receiver_id and text required")

    conn = db()
    conn.execute("INSERT INTO messages (sender_id, receiver_id, text) VALUES (?, ?, ?)", (uid, receiver_id, text))
    sender_row = conn.execute("SELECT name FROM users WHERE user_id=?", (uid,)).fetchone()
    sender_name = sender_row["name"] if sender_row and sender_row["name"] else "Пользователь"
    conn.commit()
    conn.close()

    send_telegram_notification(
        receiver_id,
        f"💬 <b>{sender_name}</b> отправил(а) вам новое сообщение в Du&Yes!\n<i>«{text[:60]}...»</i>"
    )
    return {"ok": True}


@app.get("/api/gifts")
def gifts(x_telegram_init_data: str | None = Header(default=None)):
    current_user(x_telegram_init_data)
    conn = db()
    rows = conn.execute("SELECT * FROM gifts WHERE COALESCE(is_active,1)=1 ORDER BY COALESCE(price_coins,0), gift_id").fetchall()
    conn.close()
    return {"enabled": True, "gifts": [dict(r) for r in rows]}


@app.post("/api/gifts/send")
def send_gift(data: dict, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    receiver_id = data.get("receiver_id")
    gift_id = data.get("gift_id")

    if not receiver_id or not gift_id:
        raise HTTPException(400, "receiver_id and gift_id are required")

    conn = db()
    gift = conn.execute("SELECT * FROM gifts WHERE gift_id=?", (gift_id,)).fetchone()
    if not gift:
        conn.close()
        raise HTTPException(404, "Gift not found")

    balance_row = conn.execute("SELECT coins FROM gift_balances WHERE user_id=?", (uid,)).fetchone()
    user_coins = balance_row["coins"] if balance_row else 0
    gift_price = gift["price_coins"] or 0

    if user_coins < gift_price:
        conn.close()
        raise HTTPException(400, "Недостаточно монет на балансе")

    conn.execute("UPDATE gift_balances SET coins = coins - ? WHERE user_id=?", (gift_price, uid))
    conn.execute("INSERT INTO sent_gifts (sender_id, receiver_id, gift_id) VALUES (?, ?, ?)", (uid, receiver_id, gift_id))

    sender_row = conn.execute("SELECT name FROM users WHERE user_id=?", (uid,)).fetchone()
    sender_name = sender_row["name"] if sender_row and sender_row["name"] else "Пользователь"

    conn.commit()
    conn.close()

    gift_emoji = gift["emoji"] if gift["emoji"] else "🎁"
    gift_name = gift["name_ru"] or gift["name_en"] or "Подарок"
    send_telegram_notification(
        receiver_id,
        f"{gift_emoji} <b>{sender_name}</b> отправил(а) вам подарок «{gift_name}» в Du&Yes!"
    )
    return {"ok": True}


@app.get("/api/favorites")
def favorites(x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    rows = conn.execute(
        "SELECT u.* FROM favorites f JOIN users u ON u.user_id=f.favorite_user_id WHERE f.user_id=? AND u.profile_published=1",
        (uid,),
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        p = dict(r)
        out.append({
            "user_id": p.get("user_id"),
            "name": p.get("name"),
            "age": calculate_age(p.get("birth_date")),
            "city": p.get("city"),
            "verified": p.get("verification_status") == "verified"
        })
    return {"profiles": out}


@app.post("/api/favorites/{target_id}")
def add_favorite(target_id: int, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    if uid == target_id:
        raise HTTPException(400, "Cannot favorite yourself")

    conn = db()
    conn.execute("INSERT OR IGNORE INTO favorites(user_id, favorite_user_id) VALUES(?,?)", (uid, target_id))

    me_row = conn.execute("SELECT name FROM users WHERE user_id=?", (uid,)).fetchone()
    sender_name = me_row["name"] if me_row and me_row["name"] else "Пользователь"

    conn.commit()
    conn.close()

    send_telegram_notification(
        target_id,
        f"⭐ <b>{sender_name}</b> добавил(а) вас в своё Избранное в Du&Yes!"
    )
    return {"ok": True}


@app.delete("/api/favorites/{target_id}")
def remove_favorite(target_id: int, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    conn.execute("DELETE FROM favorites WHERE user_id=? AND favorite_user_id=?", (uid, target_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/verification/request")
def request_verification(x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    conn.execute("UPDATE users SET verification_status='pending', verification_submitted_at=CURRENT_TIMESTAMP WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    return {"ok": True}


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
