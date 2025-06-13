from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import Config
from database import *
from keyboards import *
from messages import Messages
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Состояния диалога
(START, REVIEW, SCREENSHOT, 
 DATE, NAME, ARTICLE, PAYMENT_INFO) = range(7)

def escape_markdown(text):
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in str(text)])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            Messages.START,
            reply_markup=main_menu(),
            parse_mode='MarkdownV2'
        )
        return REVIEW
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Начните заново с /start",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == "✅ Уже оставил отзыв":
            await update.message.reply_text(
                Messages.REQUEST_SCREENSHOT,
                parse_mode='MarkdownV2'
            )
            return SCREENSHOT
        elif update.message.text == "🌟 Хочу оставить отзыв":
            await update.message.reply_text(
                Messages.REVIEW_INSTRUCTIONS,
                parse_mode='MarkdownV2'
            )
            return REVIEW
    except Exception as e:
        logger.error(f"Error in handle_review: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        os.makedirs("screenshots", exist_ok=True)
        file = await update.message.photo[-1].get_file()
        filename = f"screenshots/{update.message.from_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        await file.download_to_drive(filename)
        context.user_data['screenshot_path'] = filename
        
        await update.message.reply_text(
            Messages.REQUEST_DATE,
            reply_markup=date_keyboard(),
            parse_mode='MarkdownV2'
        )
        return DATE
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await update.message.reply_text(
            Messages.SCREENSHOT_ERROR,
            parse_mode='MarkdownV2',
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['review_date'] = update.message.text
        await update.message.reply_text(
            Messages.REQUEST_NAME,
            parse_mode='MarkdownV2'
        )
        return NAME
    except Exception as e:
        logger.error(f"Error in handle_date: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['reviewer_name'] = update.message.text
        await update.message.reply_text(
            Messages.REQUEST_ARTICLE,
            parse_mode='MarkdownV2'
        )
        return ARTICLE
    except Exception as e:
        logger.error(f"Error in handle_name: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['article'] = update.message.text
        await update.message.reply_text(
            Messages.REQUEST_PAYMENT_INFO,
            parse_mode='MarkdownV2'
        )
        return PAYMENT_INFO
    except Exception as e:
        logger.error(f"Error in handle_article: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.user_data.get('screenshot_path') or not context.user_data.get('review_date') or not context.user_data.get('reviewer_name') or not context.user_data.get('article'):
            raise ValueError("Не все данные собраны")
            
        context.user_data['payment_info'] = update.message.text
        username = update.message.from_user.username or update.message.from_user.full_name
        
        review_data = {
            'user_id': update.message.from_user.id,
            'username': username,
            'screenshot_path': context.user_data['screenshot_path'],
            'review_date': context.user_data['review_date'],
            'reviewer_name': context.user_data['reviewer_name'],
            'article': context.user_data['article'],
            'payment_info': context.user_data['payment_info'],
            'status': 'pending'
        }
        
        review_id = add_review(review_data)
        
        await send_to_admin(context, review_id, username)
        
        await update.message.reply_text(
            Messages.REVIEW_SUBMITTED,
            parse_mode='MarkdownV2',
            reply_markup=restart_keyboard()
        )
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in handle_payment_info: {e}")
        await update.message.reply_text(
            "Произошла ошибка при сохранении данных. Пожалуйста, начните заново с /start",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def send_to_admin(context, review_id, username):
    try:
        review = get_review_by_id(review_id)
        
        caption = Messages.ADMIN_REVIEW_CAPTION.format(
            username=escape_markdown(username),
            date=escape_markdown(review['review_date']),
            name=escape_markdown(review['reviewer_name']),
            article=escape_markdown(review['article']),
            payment_info=escape_markdown(review['payment_info'])
        )
        
        await context.bot.send_photo(
            chat_id=Config.ADMIN_GROUP_ID,
            photo=open(review['screenshot_path'], 'rb'),
            caption=caption,
            parse_mode='MarkdownV2',
            reply_markup=admin_review_keyboard(review_id)
        )
    except Exception as e:
        logger.error(f"Error sending to admin: {e}")

async def approve_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        review_id = int(query.data.split('_')[1])
        update_review_status(review_id, 'approved')
        
        review = get_review_by_id(review_id)
        
        await context.bot.send_message(
            chat_id=review['user_id'],
            text=Messages.REVIEW_APPROVED,
            parse_mode='MarkdownV2',
            reply_markup=restart_keyboard()
        )
        
        await query.edit_message_caption(
            caption=f"✅ ОДОБРЕНО\n{query.message.caption}",
            parse_mode='MarkdownV2'
        )
        
    except Exception as e:
        logger.error(f"Approve error: {e}")
        await query.answer("Ошибка при обработке", show_alert=True)

async def reject_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        review_id = int(query.data.split('_')[1])
        update_review_status(review_id, 'rejected')
        
        review = get_review_by_id(review_id)
        
        await context.bot.send_message(
            chat_id=review['user_id'],
            text=Messages.REVIEW_REJECTED,
            parse_mode='MarkdownV2',
            reply_markup=restart_keyboard()
        )
        
        await query.edit_message_caption(
            caption=f"❌ ОТКЛОНЕНО\n{query.message.caption}",
            parse_mode='MarkdownV2'
        )
        
    except Exception as e:
        logger.error(f"Reject error: {e}")
        await query.answer("Ошибка при обработке", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=True)
    
    if update.message:
        await update.message.reply_text(
            "Произошла ошибка. Начните заново с /start",
            reply_markup=restart_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.answer(
            "Произошла ошибка. Пожалуйста, попробуйте ещё раз",
            show_alert=True
        )
    return ConversationHandler.END