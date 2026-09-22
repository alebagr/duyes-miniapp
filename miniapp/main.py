import hashlib
import hmac
import json
import os
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Автоматически создаем папку static, если ее нет
STATIC_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = os.getenv("DB_NAME", "duyes.db")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
INIT_DATA_MAX_AGE = int(os.getenv("MINIAPP_INIT_DATA_MAX_AGE", "86400"))

app = FastAPI(title="Du&Yes Mini App API", version="1.0.0")

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


def table_columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


@app.get("/api/health")
def health():
    return {"ok": True, "service": "duyes-miniapp"}


@app.get("/api/me")
def me(x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if not row:
        return {"registered": False, "user_id": uid}
    data = dict(row)
    data["age"] = calculate_age(data.get("birth_date"))
    data["verification_status"] = data.get("verification_status", "none")
    return {"registered": True, "user": data}


@app.get("/api/profiles")
def profiles(
    x_telegram_init_data: str | None = Header(default=None),
    country: str | None = None,
    city: str | None = None,
    min_age: int | None = Query(default=None, ge=18, le=100),
    max_age: int | None = Query(default=None, ge=18, le=100),
    online: bool = False,
):
    uid = current_user(x_telegram_init_data)
    conn = db()
    me_row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if not me_row:
        conn.close()
        return {"profiles": []}
    gender = me_row["gender"]
    opposite = "female" if str(gender).lower() in {"male", "мужчина", "м"} else "male"
    rows = conn.execute(
        "SELECT * FROM users WHERE profile_published=1 AND profile_blocked=0 AND user_id<>? AND gender=?",
        (uid, opposite),
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
        if online and not p.get("online"):
            continue
        result.append({
            "user_id": p.get("user_id"),
            "name": p.get("name"),
            "age": age,
            "country": p.get("country"),
            "region": p.get("region"),
            "city": p.get("city"),
            "photo_1_file_id": p.get("photo_1_file_id"),
            "photo_2_file_id": p.get("photo_2_file_id"),
            "photos_hidden": p.get("photos_hidden", 0),
            "previously_married": p.get("previously_married", 0),
            "children": p.get("children", 0),
            "online": bool(p.get("online")),
            "verified": p.get("verification_status") == "verified",
        })
    return {"profiles": result}


@app.get("/api/gifts")
def gifts(x_telegram_init_data: str | None = Header(default=None)):
    current_user(x_telegram_init_data)
    conn = db()
    enabled = conn.execute("SELECT value FROM settings WHERE key='GIFTS_ENABLED'").fetchone()
    enabled_value = enabled and str(enabled[0]).lower() in {"1", "true", "yes", "on"}
    cols = table_columns(conn, "gifts") if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gifts'").fetchone() else set()
    if not cols:
        conn.close()
        return {"enabled": enabled_value, "gifts": []}
    rows = conn.execute("SELECT * FROM gifts WHERE COALESCE(is_active,1)=1 ORDER BY COALESCE(price_coins,0), gift_id").fetchall()
    conn.close()
    return {"enabled": enabled_value, "gifts": [dict(r) for r in rows]}


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
        out.append({"user_id": p.get("user_id"), "name": p.get("name"), "age": calculate_age(p.get("birth_date")), "city": p.get("city"), "photo_1_file_id": p.get("photo_1_file_id"), "verified": p.get("verification_status") == "verified"})
    return {"profiles": out}


@app.post("/api/favorites/{target_id}")
def add_favorite(target_id: int, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    if uid == target_id:
        raise HTTPException(400, "Cannot favorite yourself")
    conn = db()
    conn.execute("INSERT OR IGNORE INTO favorites(user_id, favorite_user_id) VALUES(?,?)", (uid, target_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/favorites/{target_id}")
def remove_favorite(target_id: int, x_telegram_init_data: str | None = Header(default=None)):
    uid = current_user(x_telegram_init_data)
    conn = db()
    conn.execute("DELETE FROM favorites WHERE user_id=? AND favorite_user_id=?", (uid, target_id))
    conn.commit()
    conn.close()
    return {"ok": True}


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
