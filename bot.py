import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from config import Config
from handlers import *
from database import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Starting bot...")
    
    try:
        app = Application.builder().token(Config.BOT_TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                REVIEW: [
                    MessageHandler(filters.Regex(r'^(🌟 Хочу оставить отзыв|✅ Уже оставил отзыв)$'), handle_review)
                ],
                SCREENSHOT: [
                    MessageHandler(filters.PHOTO, handle_screenshot),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                        lambda u, c: u.message.reply_text(
                            Messages.SCREENSHOT_ERROR,
                            parse_mode='MarkdownV2',
                            reply_markup=restart_keyboard()
                        ))
                ],
                DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date)
                ],
                NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
                ],
                ARTICLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_article)
                ],
                PAYMENT_INFO: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment_info)
                ]
            },
            fallbacks=[CommandHandler('start', start)],
            allow_reentry=True
        )
        
        app.add_handler(conv_handler)
        app.add_handler(CallbackQueryHandler(approve_review, pattern=r'^approve_\d+$'))
        app.add_handler(CallbackQueryHandler(reject_review, pattern=r'^reject_\d+$'))
        app.add_handler(CommandHandler('start', start))
        app.add_error_handler(error_handler)
        
        logger.info("✅ Bot is ready")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.critical(f"🔥 Failed to start bot: {e}")

if __name__ == '__main__':
    init_db()
    main()