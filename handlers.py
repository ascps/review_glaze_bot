from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, filters
from config import Config
from database import *
from keyboards import *
from messages import Messages
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Константы канала
CHANNEL_ID = -1002687212900
CHANNEL_LINK = "https://t.me/mrnicktestbot"

# Состояния диалога
(START, REVIEW, SCREENSHOT, DATE, NAME, ARTICLE, PAYMENT_INFO) = range(7)

def escape_markdown(text):
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in str(text)])

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {str(e)}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            Messages.START,
            reply_markup=main_menu(),
            parse_mode='MarkdownV2'
        )
        return REVIEW
    except Exception as e:
        logger.error(f"Ошибка в start: {str(e)}")
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
        logger.error(f"Ошибка в handle_review: {str(e)}")
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
        logger.error(f"Ошибка обработки фото: {str(e)}")
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
        logger.error(f"Ошибка в handle_date: {str(e)}")
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
        logger.error(f"Ошибка в handle_name: {str(e)}")
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
        logger.error(f"Ошибка в handle_article: {str(e)}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз",
            reply_markup=restart_keyboard()
        )
        return ConversationHandler.END

async def handle_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not all(key in context.user_data for key in ['screenshot_path', 'review_date', 'reviewer_name', 'article']):
            raise ValueError("Не все данные собраны")
            
        payment_info = update.message.text
        context.user_data['payment_info'] = payment_info
        
        username = update.message.from_user.username or update.message.from_user.full_name
        
        review_data = {
            'user_id': update.message.from_user.id,
            'username': username,
            'screenshot_path': context.user_data['screenshot_path'],
            'review_date': context.user_data['review_date'],
            'reviewer_name': context.user_data['reviewer_name'],
            'article': context.user_data['article'],
            'payment_info': payment_info,
            'status': 'pending'
        }
        
        review_id = add_review(review_data)
        await send_to_admin(context, review_id, username)
        
        await update.message.reply_text(
            f"✅ Ваш отзыв получен! Мы проверим его в течение 24 часов.\n\n"
            f"🎁 Участвуйте в розыгрыше защитных стёкол!\n"
            f"1. Подпишитесь на наш канал: {CHANNEL_LINK}\n"
            f"2. Нажмите кнопку ниже",
            reply_markup=giveaway_keyboard()
        )
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Ошибка в handle_payment_info: {str(e)}")
        await update.message.reply_text(
            "Произошла ошибка. Нажмите /start",
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
        logger.error(f"Ошибка отправки админу: {str(e)}")

async def approve_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer("Обработка...")
        review_id = int(query.data.split('_')[1])
        
        update_review_status(review_id, 'approved')
        review = get_review_by_id(review_id)
        
        await context.bot.send_message(
            chat_id=review['user_id'],
            text=Messages.REVIEW_APPROVED,
            parse_mode='MarkdownV2'
        )
        
        await query.edit_message_caption(
            caption=f"✅ ОДОБРЕНО\n{query.message.caption}",
            parse_mode='MarkdownV2',
            reply_markup=None
        )
        
    except Exception as e:
        logger.error(f"Ошибка approve_review: {str(e)}")
        await query.answer("⚠️ Ошибка! Попробуйте позже", show_alert=True)

async def reject_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer("Обработка...")
        review_id = int(query.data.split('_')[1])
        
        update_review_status(review_id, 'rejected')
        review = get_review_by_id(review_id)
        
        await context.bot.send_message(
            chat_id=review['user_id'],
            text=Messages.REVIEW_REJECTED,
            parse_mode='MarkdownV2'
        )
        
        await query.edit_message_caption(
            caption=f"❌ ОТКЛОНЕНО\n{query.message.caption}",
            parse_mode='MarkdownV2',
            reply_markup=None
        )
        
    except Exception as e:
        logger.error(f"Ошибка reject_review: {str(e)}")
        await query.answer("⚠️ Ошибка! Попробуйте позже", show_alert=True)

async def handle_giveaway_participation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer("Проверка...")
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.full_name
        name = context.user_data.get('reviewer_name', username)
        
        is_subscribed = await check_subscription(user_id, context)
        if not is_subscribed:
            await query.edit_message_text(
                Messages.GIVEAWAY_NOT_SUBSCRIBED.format(channel_link=CHANNEL_LINK),
                parse_mode='MarkdownV2',
                reply_markup=giveaway_keyboard()
            )
            return

        success = add_giveaway_participant(user_id, username, name)
        if success:
            await query.edit_message_text(
                Messages.GIVEAWAY_SUCCESS.format(
                    participant_id=user_id,
                    name=name,
                    next_draw_date="10 числа следующего месяца",
                    channel_link=CHANNEL_LINK
                ),
                parse_mode='MarkdownV2',
                reply_markup=after_giveaway_keyboard()
            )
        else:
            await query.edit_message_text(
                Messages.GIVEAWAY_ALREADY_PARTICIPATING.format(channel_link=CHANNEL_LINK),
                parse_mode='MarkdownV2',
                reply_markup=after_giveaway_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка handle_giveaway_participation: {str(e)}")
        await query.answer("⚠️ Ошибка! Попробуйте позже", show_alert=True)

async def handle_check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        user_id = query.from_user.id
        is_subscribed = await check_subscription(user_id, context)
        
        if is_subscribed:
            text = "✅ Вы подписаны на канал! Можете участвовать в розыгрыше."
        else:
            text = f"❌ Вы не подписаны. Подпишитесь: {CHANNEL_LINK}"
            
        await query.edit_message_text(
            text,
            reply_markup=giveaway_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка handle_check_subscription: {str(e)}")
        await query.answer("⚠️ Ошибка проверки", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = str(context.error)
    logger.error(f"❌ Ошибка: {error}")
    
    if update and update.message:
        await update.message.reply_text(
            "Произошла ошибка. Нажмите /start",
            reply_markup=restart_keyboard()
        )
    elif update and update.callback_query:
        await update.callback_query.answer(
            "Ошибка. Попробуйте ещё раз",
            show_alert=True
        )
    return ConversationHandler.END