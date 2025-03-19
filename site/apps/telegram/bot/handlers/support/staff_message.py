from aiogram import Router, types
from bot_loader import support_bot
from django.conf import settings
from core.loading import get_model

TelegramSupportChat = get_model("telegram", "TelegramSupportChat")

staff_router = Router()


@staff_router.message(
    content_types=types.ContentType.TEXT, chat_id=settings.TELEGRAM_SUPPORT_CHAT_ID
)
async def handle_operator_message(message: types.Message):
    # Проверяем, из топика ли сообщение
    if message.message_thread_id:
        # Ищем пользователя по топику
        user_id = next(
            (
                uid
                for uid, tid in TelegramSupportChat.objects.values_list(
                    "telegram_id", "chat_id"
                )
                if tid == message.message_thread_id
            ),
            None,
        )
        if user_id:
            # Отправляем сообщение пользователю
            await support_bot.send_message(
                user_id, f"Ответ от оператора:\n{message.text}"
            )
