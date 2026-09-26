from admin import is_admin, create_test_account, get_test_accounts

# Набор из 8 реалистичных тестовых анкет
TEST_PROFILES_DATA = [
    {
        "first_name": "Мария",
        "gender": "female",
        "birth_date": "15.05.1998",
        "country": "Армения",
        "city": "Ереван",
        "about": "Изучаю веб-разработку, обожаю горы и походы на выходных.",
        "photo_1": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=500",
        "photo_2": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=500"
    },
    {
        "first_name": "Тигран",
        "gender": "male",
        "birth_date": "20.11.1995",
        "country": "Армения",
        "city": "Ереван",
        "about": "Музыкант, играю на гитаре. Ищу интересных людей для общения.",
        "photo_1": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=500",
        "photo_2": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=500"
    },
    {
        "first_name": "Ани",
        "gender": "female",
        "birth_date": "10.02.2001",
        "country": "Армения",
        "city": "Гюмри",
        "about": "Люблю фотографию, искусство и долгие прогулки по вечернему городу.",
        "photo_1": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500",
        "photo_2": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=500"
    },
    {
        "first_name": "Давид",
        "gender": "male",
        "birth_date": "05.08.1993",
        "country": "Армения",
        "city": "Ереван",
        "about": "Занимаюсь IT, увлекаюсь шахматами и настольными играми.",
        "photo_1": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500",
        "photo_2": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=500"
    },
    {
        "first_name": "Светлана",
        "gender": "female",
        "birth_date": "12.12.1997",
        "country": "Армения",
        "city": "Ванадзор",
        "about": "Дизайнер интерьеров. Ценю искренность и чувство юмора.",
        "photo_1": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=500",
        "photo_2": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=500"
    },
    {
        "first_name": "Артур",
        "gender": "male",
        "birth_date": "30.03.1990",
        "country": "Армения",
        "city": "Ереван",
        "about": "Архитектор. Люблю старый город и хороший кофе в уютных кофейнях.",
        "photo_1": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=500",
        "photo_2": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=500"
    },
    {
        "first_name": "Мариам",
        "gender": "female",
        "birth_date": "22.07.1999",
        "country": "Армения",
        "city": "Ереван",
        "about": "Студентка медицинского. Увлекаюсь литературой и психологией.",
        "photo_1": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=500",
        "photo_2": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500"
    },
    {
        "first_name": "Гор",
        "gender": "male",
        "birth_date": "14.01.1996",
        "country": "Армения",
        "city": "Дилижан",
        "about": "Живу среди лесов Дилижана. Занимаюсь видеосъемкой и туризмом.",
        "photo_1": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=500",
        "photo_2": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500"
    }
]

def generate_up_to_8_test_accounts(admin_user_id):
    """
    Создает до 8 тестовых аккаунтов с аккаунта администратора,
    если они еще не были созданы.
    """
    if not is_admin(admin_user_id):
        return {"success": False, "reason": "Доступ запрещен. Вы не администратор."}

    # Проверяем, сколько тестовых аккаунтов уже есть
    existing_accounts = get_test_accounts()
    existing_count = len(existing_accounts)

    if existing_count >= 8:
        return {"success": True, "message": "Уже создано максимальное количество тестовых анкет (8).", "created": 0}

    to_create_count = 8 - existing_count
    created_ids = []

    for i in range(to_create_count):
        profile_data = TEST_PROFILES_DATA[existing_count + i]
        result = create_test_account(
            user_id=admin_user_id,
            first_name=profile_data["first_name"],
            gender=profile_data["gender"],
            birth_date=profile_data["birth_date"],
            country=profile_data["country"],
            city=profile_data["city"],
            about=profile_data["about"],
            photo_1=profile_data["photo_1"],
            photo_2=profile_data["photo_2"]
        )
        if result.get("success"):
            created_ids.append(result.get("user_id"))

    return {
        "success": True,
        "message": f"Успешно создано тестовых анкет: {len(created_ids)}",
        "created_ids": created_ids
    }
