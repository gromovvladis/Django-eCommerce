from aiogram import Router, types

from django.conf import settings

from oscar.core.loading import get_model

from bot_loader import support_bot

customer_router = Router()

TelegramSupportChat = get_model("telegram", "TelegramSupportChat")


@customer_router.message(content_types=types.ContentType.TEXT)
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "---"
    first_name = message.from_user.first_name or "Аноним"

    # Проверяем, есть ли активный чат для пользователя
    if user_id not in TelegramSupportChat.objects.values_list("telegram_id", flat=True):
        # Создаем новый топик
        topic = await support_bot.create_forum_topic(
            chat_id=settings.TELEGRAM_SUPPORT_CHAT_ID,
            name=f"Клиент: {user_id} ({username})",
        )
        TelegramSupportChat.objects.create(
            telegram_id=user_id,
            chat_id=topic.message_thread_id,
        )

        await support_bot.send_message(
            settings.TELEGRAM_SUPPORT_CHAT_ID,
            f"Новый клиент {first_name} ({username}, ID: {user_id}) начал чат. Перейдите в топик.",
            message_thread_id=topic.message_thread_id,
        )

    # Пересылаем сообщение пользователя в топик
    await support_bot.send_message(
        settings.TELEGRAM_SUPPORT_CHAT_ID,
        f"Сообщение от пользователя {first_name} ({user_id}):\n{message.text}",
        message_thread_id=TelegramSupportChat.objects.get(telegram_id=user_id),
    )
    await message.reply("Ваше сообщение отправлено в поддержку.")
