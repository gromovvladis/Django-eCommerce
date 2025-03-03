from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from oscar.core.loading import get_model

Staff = get_model("user", "Staff")


def get_notif_keyboard(telegram_id):
    try:
        staff = Staff.objects.get(telegram_id=telegram_id)
        notification_codes = set(
            staff.user.notification_settings.values_list("code", flat=True)
        )

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
            [InlineKeyboardButton(text="Готово", callback_data="done")],
        ]
    except Staff.DoesNotExist:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Настройки невозможно изменить. Телеграм не связан с профилем персонала.",
                    callback_data="success",
                )
            ]
        ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
