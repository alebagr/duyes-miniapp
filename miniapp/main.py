from datetime import date, datetime
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

# Твой модуль проверки фото (имя функции зависит от реализации, здесь подставлен стандартный вызов)
from photo_compare import check_registration_photos

router = APIRouter(prefix="/api", tags=["Registration"])


def validate_user_age(birth_date_str: str) -> int | None:
    """Строгая проверка возраста пользователя: строго от 18 до 72 лет."""
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


@router.post("/register")
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
    # 1. Проверяем возраст (диапазон 18-72)
    age = validate_user_age(birth_date)
    if not age:
        raise HTTPException(
            status_code=400,
            detail=(
                "Регистрация возможна только для пользователей в возрасте от"
                " 18 до 72 лет."
            ),
        )

    # 2. Читаем байты обеих фотографий
    p1_bytes = await photo_1.read()
    p2_bytes = await photo_2.read()

    # Здесь извлекается telegram_id из x_telegram_init_data (или используется заглушка для теста)
    user_id = 1001  # Замени на получение реального ID из initData при необходимости

    # 3. Проверка фотографий через твой модуль photo_compare.py
    try:
        photo_check = check_registration_photos(user_id, p1_bytes, p2_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при проверке фотографий: {str(e)}",
        )

    if photo_check and photo_check.get("status") == "rejected":
        reason = photo_check.get(
            "reason", "Фото не соответствуют правилам сервиса."
        )
        raise HTTPException(status_code=400, detail=f"Фото отклонены: {reason}")

    # 4. Сохранение данных пользователя в базу данных (твоя существующая логика БД)
    # db_save_user(...)

    return {
        "status": "success",
        "message": "Регистрация успешно завершена!",
    }
