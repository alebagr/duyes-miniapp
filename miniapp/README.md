# Du&Yes Mini App

Премиальный mobile-first Mini App для Du&Yes внутри Telegram.

## Что подготовлено
- Telegram Mini App SDK.
- Серверная проверка `Telegram.WebApp.initData` через HMAC-SHA256.
- `/api/me`.
- `/api/profiles` с фильтрами и противоположным полом.
- `/api/favorites`.
- `/api/gifts` с флагом `GIFTS_ENABLED`.
- фирменная тёмно-синяя/золотая тема Du&Yes.
- адаптация под safe area Telegram.
- нижняя навигация: Главная / Поиск / Избранное / Сообщения / Профиль.
- подготовлен экран подарков.

## Переменные окружения
- `BOT_TOKEN` — токен Telegram-бота.
- `DB_NAME` — путь к общей `duyes.db`.
- `MINIAPP_INIT_DATA_MAX_AGE` — срок действия initData, по умолчанию 86400 секунд.

## Запуск
```bash
pip install -r requirements-miniapp.txt
uvicorn miniapp.main:app --host 0.0.0.0 --port 8000
```

Для Telegram нужен HTTPS URL. В @BotFather Mini App можно настроить как Main Mini App или Menu Button.

## Важно
`Telegram.WebApp.initDataUnsafe` не используется для авторизации. Сервер принимает и проверяет только `initData` из Telegram.
