from telegram import Bot
import asyncio

BOT_TOKEN = "7752249517:AAFIjVtIoj6v-BtCddSGgPVcOTeCa9CQNMk"
CHANNEL_USERNAME = "@mrnicktestbot"  # замените на ваш username

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        message = await bot.send_message(chat_id=CHANNEL_USERNAME, text="🔍 Проверка доступа бота.")
        print(f"✅ Успех! Chat ID канала: {message.chat.id}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
