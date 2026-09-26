from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import os

app = FastAPI()

# HTML-интерфейс (встроен прямо в бэкенд для гарантированного обновления)
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Du&Yes</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #121420 0%, #1a1c2e 100%);
            margin: 0;
            padding: 16px;
            color: #fff;
            min-height: 100vh;
        }
        .container {
            max-width: 440px;
            margin: 0 auto;
            background: rgba(26, 28, 46, 0.95);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }
        h2 {
            text-align: center;
            color: #ffb703;
            margin-bottom: 20px;
            font-size: 22px;
        }
        label {
            display: block;
            margin: 14px 0 6px 0;
            font-weight: 500;
            font-size: 14px;
            color: #e0e0e0;
        }
        input, select, textarea {
            width: 100%;
            padding: 12px 14px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.15);
            background: rgba(255,255,255,0.05);
            color: #fff;
            box-sizing: border-box;
            font-size: 15px;
            outline: none;
            transition: border-color 0.2s;
        }
        input:focus, select:focus, textarea:focus {
            border-color: #ffb703;
        }
        select option {
            background: #1a1c2e;
            color: #fff;
        }
        textarea {
            resize: vertical;
            min-height: 80px;
        }
        .btn-submit {
            width: 100%;
            margin-top: 24px;
            padding: 14px;
            background: linear-gradient(135deg, #ffb703 0%, #fb8500 100%);
            color: #121420;
            border: none;
            border-radius: 12px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(251,133,0,0.3);
        }
        .error {
            background: rgba(198,40,40,0.2);
            border: 1px solid #c62828;
            color: #ff8a80;
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            margin-bottom: 15px;
            display: none;
        }
        .photo-section {
            margin-top: 15px;
            background: rgba(255,255,255,0.03);
            padding: 12px;
            border-radius: 12px;
            border: 1px dashed rgba(255,255,255,0.2);
        }
        .geo-status {
            font-size: 13px;
            color: #ffb703;
            margin-top: 6px;
            text-align: center;
        }
        .btn-geo {
            width: 100%;
            margin-top: 8px;
            padding: 12px;
            background: rgba(255,183,3,0.15);
            color: #ffb703;
            border: 1px solid rgba(255,183,3,0.4);
            border-radius: 12px;
            font-weight: 500;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-geo:active {
            background: rgba(255,183,3,0.3);
        }
    </style>
</head>
<body>

<div class="container" id="screen-register">
    <h2>Регистрация</h2>
    <div id="reg-error" class="error"></div>

    <form id="registration-form" onsubmit="submitRegistration(event)">
        <label>Ваше имя:</label>
        <input type="text" id="reg-name" maxlength="15" placeholder="Имя" required>

        <label>Пол:</label>
        <select id="reg-gender">
            <option value="male">Мужской</option>
            <option value="female">Женский</option>
        </select>

        <label>Дата рождения (вам должно быть 18+):</label>
        <input type="text" id="reg-birth" placeholder="ДД.ММ.ГГГГ или ГГГГ-ММ-ДД" required>

        <label>Местоположение (обязательно):</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <input type="text" id="reg-country" placeholder="Страна" readonly required style="background: rgba(255,255,255,0.02); color: #aaa;">
            <input type="text" id="reg-city" placeholder="Город" readonly required style="background: rgba(255,255,255,0.02); color: #aaa;">
        </div>
        <button type="button" class="btn-geo" onclick="requestUserLocation()">📍 Разрешить и определить геолокацию</button>
        <div id="geo-status-text" class="geo-status">Геолокация обязательна для продолжения</div>

        <label>Семейное положение:</label>
        <select id="reg-married">
            <option value="no">Не состоял(а) в браке</option>
            <option value="yes">Состоял(а) в браке</option>
        </select>

        <label>Дети:</label>
        <select id="reg-children">
            <option value="no">Нет детей</option>
            <option value="yes">Есть дети</option>
        </select>

        <label>О себе:</label>
        <textarea id="reg-about" placeholder="Расскажите о себе, ваших ценностях и целях..."></textarea>

        <div class="photo-section">
            <label style="margin-top:0;">Фотография 1 (Основная):</label>
            <input type="file" id="photo1" accept="image/*" required style="margin-bottom:10px;">
            <label>Фотография 2 (Дополнительная):</label>
            <input type="file" id="photo2" accept="image/*" required>
        </div>

        <button type="submit" class="btn-submit">Завершить регистрацию</button>
    </form>
</div>

<!-- Лента анкет (скрыта до регистрации) -->
<div class="container" id="screen-feed" style="display:none; padding:0; overflow:hidden;">
    <img id="feed-photo" src="" alt="Фото" style="width:100%; height:380px; object-fit:cover;">
    <div style="padding: 20px;">
        <h2 id="feed-name-age" style="text-align:left; margin:0 0 6px 0; color:#fff;"></h2>
        <p id="feed-location" style="margin:0 0 12px 0; font-weight:600; color:#ffb703;"></p>
        <p id="feed-about" style="margin:0; color:#ccc; line-height:1.4;"></p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px;">
            <button onclick="feedAction('favorite')" id="feed-fav-btn" style="padding:12px; border-radius:10px; border:none; background:rgba(255,255,255,0.1); color:#fff; font-weight:bold; cursor:pointer;">⭐ В избранное</button>
            <button onclick="alert('Чат открывается')" style="padding:12px; border-radius:10px; border:none; background:#2e7d32; color:#fff; font-weight:bold; cursor:pointer;">💬 Написать</button>
            <button onclick="feedAction('block')" style="padding:12px; border-radius:10px; border:none; background:rgba(198,40,40,0.3); color:#ff8a80; font-weight:bold; cursor:pointer;">🚫 Блок</button>
            <button onclick="feedAction('report')" style="padding:12px; border-radius:10px; border:none; background:rgba(245,127,23,0.3); color:#ffb703; font-weight:bold; cursor:pointer;">⚠️ Жалоба</button>
        </div>
        <button onclick="nextProfile()" style="width:100%; margin-top: 15px; padding: 14px; background: #ffb703; color: #121420; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px;">➡️ Следующая анкета</button>
    </div>
</div>

<script>
let tg = window.Telegram?.WebApp;
if (tg) tg.expand();

let userLatitude = null;
let userLongitude = null;
let isGeoVerified = false;

function requestUserLocation() {
    const statusText = document.getElementById('geo-status-text');
    statusText.innerText = "⏳ Запрос геолокации...";
    statusText.style.color = "#ffb703";

    if (window.Telegram?.WebApp?.LocationManager) {
        const lm = window.Telegram.WebApp.LocationManager;
        lm.init(() => {
            if (lm.isInited) {
                lm.getLocation((data) => {
                    if (data && data.latitude && data.longitude) {
                        setCoords(data.latitude, data.longitude);
                    } else {
                        fallbackBrowserGeolocation();
                    }
                });
            } else {
                fallbackBrowserGeolocation();
            }
        });
    } else {
        fallbackBrowserGeolocation();
    }
}

function fallbackBrowserGeolocation() {
    const statusText = document.getElementById('geo-status-text');
    if (!navigator.geolocation) {
        statusText.innerText = "❌ Геолокация не поддерживается устройством";
        statusText.style.color = "#ff8a80";
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            setCoords(position.coords.latitude, position.coords.longitude);
        },
        (error) => {
            statusText.innerText = "❌ Доступ к геолокации отклонен. Регистрация невозможна.";
            statusText.style.color = "#ff8a80";
            isGeoVerified = false;
        },
        { timeout: 10000, enableHighAccuracy: true }
    );
}

function setCoords(lat, lon) {
    userLatitude = lat;
    userLongitude = lon;
    isGeoVerified = true;
    
    document.getElementById('reg-country').value = "Армения";
    document.getElementById('reg-city').value = "Ереван";
    
    const statusText = document.getElementById('geo-status-text');
    statusText.innerText = "✅ Геолокация успешно подтверждена!";
    statusText.style.color = "#4caf50";

    const btnGeo = document.querySelector('.btn-geo');
    if (btnGeo) {
        btnGeo.innerText = "📍 Местоположение определено";
        btnGeo.style.background = "rgba(76, 175, 80, 0.15)";
        btnGeo.style.borderColor = "rgba(76, 175, 80, 0.4)";
        btnGeo.style.color = "#4caf50";
    }
}

function validateAge(dateStr) {
    const parts = dateStr.includes('.') ? dateStr.split('.') : dateStr.split('-');
    if (parts.length !== 3) return false;
    const [day, month, year] = dateStr.includes('.') ? parts.map(Number) : [parts[2], parts[1], parts[0]].map(Number);
    const birthDate = new Date(year, month - 1, day);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    return age >= 18 && age <= 72;
}

async function submitRegistration(event) {
    event.preventDefault();
    const errBox = document.getElementById('reg-error');
    errBox.style.display = 'none';

    if (!isGeoVerified) {
        errBox.innerText = "Ошибка: Необходимо разрешить и подтвердить геолокацию перед регистрацией.";
        errBox.style.display = 'block';
        return;
    }

    const birthDate = document.getElementById('reg-birth').value.trim();
    if (!validateAge(birthDate)) {
        errBox.innerText = "Ошибка: Возраст должен быть строго от 18 до 72 лет.";
        errBox.style.display = 'block';
        return;
    }

    const p1 = document.getElementById('photo1').files[0];
    const p2 = document.getElementById('photo2').files[0];
    if (!p1 || !p2) {
        errBox.innerText = "Пожалуйста, загрузите обе фотографии.";
        errBox.style.display = 'block';
        return;
    }

    const formData = new FormData();
    formData.append('first_name', document.getElementById('reg-name').value.trim());
    formData.append('gender', document.getElementById('reg-gender').value);
    formData.append('birth_date', birthDate);
    formData.append('country', document.getElementById('reg-country').value.trim());
    formData.append('country_code', 'AM');
    formData.append('city', document.getElementById('reg-city').value.trim());
    formData.append('latitude', userLatitude);
    formData.append('longitude', userLongitude);
    formData.append('married', document.getElementById('reg-married').value);
    formData.append('children', document.getElementById('reg-children').value);
    formData.append('about', document.getElementById('reg-about').value.trim());
    formData.append('photo_1', p1);
    formData.append('photo_2', p2);

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'X-Telegram-Init-Data': tg?.initData || '' },
            body: formData
        });
        const data = await res.json();
        if (!res.ok) {
            errBox.innerText = data.detail || "Ошибка регистрации";
            errBox.style.display = 'block';
            return;
        }

        document.getElementById('screen-register').style.display = 'none';
        document.getElementById('screen-feed').style.display = 'block';
        loadFeed();
    } catch (e) {
        errBox.innerText = "Ошибка соединения с сервером";
        errBox.style.display = 'block';
    }
}

let feedProfiles = [];
let feedIndex = 0;

async function loadFeed() {
    try {
        const res = await fetch('/api/search/feed', {
            headers: { 'X-Telegram-Init-Data': tg?.initData || '' }
        });
        const data = await res.json();
        feedProfiles = data.profiles || [];
        renderFeedProfile();
    } catch (e) {
        console.error("Ошибка загрузки ленты", e);
    }
}

function renderFeedProfile() {
    if (feedIndex >= feedProfiles.length) {
        document.getElementById('screen-feed').innerHTML = "<h2 style='text-align:center; padding:40px; color:#fff;'>✨ Больше анкет нет</h2>";
        return;
    }
    const p = feedProfiles[feedIndex];
    document.getElementById('feed-photo').src = p.photo;
    document.getElementById('feed-name-age').innerText = `${p.first_name}, ${p.age}`;
    document.getElementById('feed-location').innerText = `📍 ${p.location}`;
    document.getElementById('feed-about').innerText = p.about || 'Без описания';
}

async function feedAction(action) {
    if (feedIndex >= feedProfiles.length) return;
    const targetId = feedProfiles[feedIndex].id;
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');

    await fetch('/api/search/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Telegram-Init-Data': tg?.initData || '' },
        body: JSON.stringify({ target_user_id: targetId, action: action })
    });

    if (action === 'block') nextProfile();
    if (action === 'favorite') {
        const btn = document.getElementById('feed-fav-btn');
        btn.style.background = 'rgba(255,183,3,0.2)';
        btn.style.color = '#ffb703';
        btn.innerText = '⭐ В избранном';
    }
}

function nextProfile() {
    feedIndex++;
    renderFeedProfile();
}
</script>
</body>
</html>
"""

# Корневой маршрут
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    return HTML_CONTENT

@app.get("/app/", response_class=HTMLResponse)
async def serve_mini_app():
    return HTML_CONTENT

# --- Эндпоинты бэкенда ---

@app.post("/api/register")
async def api_register(
    first_name: str = Form(...),
    gender: str = Form(...),
    birth_date: str = Form(...),
    country: str = Form(...),
    country_code: str = Form(...),
    city: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    married: str = Form(...),
    children: str = Form(...),
    about: str = Form(...),
    photo_1: UploadFile = File(...),
    photo_2: UploadFile = File(...)
):
    return {"status": "success", "message": "Регистрация успешно завершена"}

@app.get("/api/search/feed")
async def api_search_feed():
    return {
        "profiles": [
            {
                "id": 1,
                "first_name": "Анна",
                "age": 25,
                "location": "🇦🇲 Ереван, Армения",
                "about": "Люблю путешествия, искусство и хороший кофе.",
                "photo": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=500"
            }
        ]
    }

@app.post("/api/search/action")
async def api_search_action(data: dict):
    return {"status": "ok"}
