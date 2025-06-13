from telegram.ext import filters

class CustomFilters:
    @staticmethod
    def subscribed_channel():
        async def func(update, context):
            if not context.bot_data.get('channel_id'):
                return False
            try:
                member = await context.bot.get_chat_member(
                    chat_id=context.bot_data['channel_id'],
                    user_id=update.effective_user.id
                )
                return member.status in ['member', 'administrator', 'creator']
            except Exception:
                return False
        return filters.create(func)