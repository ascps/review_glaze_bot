from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌟 Хочу оставить отзыв")],
        [KeyboardButton("✅ Уже оставил отзыв")]
    ], resize_keyboard=True, one_time_keyboard=True)

def date_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🗓️ Сегодня"), KeyboardButton("📅 Вчера")],
        [KeyboardButton("⏳ Другая дата")]
    ], resize_keyboard=True, one_time_keyboard=True)

def restart_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("/start")]
    ], resize_keyboard=True, one_time_keyboard=True)

def admin_review_keyboard(review_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{review_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{review_id}")
        ]
    ])