from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async
from apps.telegram.bot.const_texts import success_text
from core.loading import get_model

User = get_model("user", "User")


async def get_notif_keyboard(telegram_id):
    try:
        user = await User.objects.aget(telegram_id=telegram_id)
        notification_codes = await sync_to_async(
            lambda: list(user.notification_settings.values_list("code", flat=True))
        )()
        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{'✅' if 'sell' in notification_codes else '❌'} Только уведомления о новых заказах",
                    callback_data="sell",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'✅' if 'status' in notification_codes else '❌'} Уведомления об изменении заказов и новых заказах",
                    callback_data="status",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'✅' if 'stock' in notification_codes else '❌'} Уведомления о товарных остатках",
                    callback_data="stock",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'✅' if 'technical' in notification_codes else '❌'} Технические уведомления (Администратор)",
                    callback_data="technical",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'✅' if 'error' in notification_codes else '❌'} Уведомления об ошибках",
                    callback_data="error",
                )
            ],
            [InlineKeyboardButton(text="Готово", callback_data=success_text)],
        ]
    except User.DoesNotExist:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Настройки невозможно изменить. Телеграм не связан с профилем персонала.",
                    callback_data=success_text,
                )
            ]
        ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
