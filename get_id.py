from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

TOKEN = "7752249517:AAFIjVtIoj6v-BtCddSGgPVcOTeCa9CQNMk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    await update.message.reply_text("Привет! Добавь меня в канал как админа, и я пришлю его ID.")

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет ID канала"""
    chat_id = update.channel_post.chat.id
    chat_title = update.channel_post.chat.title
    await update.channel_post.reply_text(
        f"🔹 ID этого канала: `{chat_id}`\n"
        f"🔹 Название: {chat_title}\n\n"
        "Используй этот ID для управления ботом в канале.",
        parse_mode="Markdown"
    )

def main():
    # Создаем Application вместо Updater
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()