from django.urls import reverse_lazy

OSCAR_HOMEPAGE = reverse_lazy("page:homepage")

# Dynamic class loading
OSCAR_DYNAMIC_CLASS_LOADER = "oscar.core.loading.default_class_loader"

OSCAR_DEFAULT_COOKIE_LIFETIME = 7 * 24 * 60 * 60

# Store cookies settings
OSCAR_STORE_COOKIE_LIFETIME = 7 * 24 * 60 * 60

# Basket settings
OSCAR_BASKET_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_BASKET_COOKIE_OPEN = "open_basket"
OSCAR_BASKET_COOKIE_SECURE = False
OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 99

# Recently-viewed products
OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_RECENTLY_VIEWED_COOKIE_NAME = "history"
OSCAR_RECENTLY_VIEWED_COOKIE_SECURE = False
OSCAR_RECENTLY_VIEWED_PRODUCTS = 10

# Currency
OSCAR_DEFAULT_CURRENCY = "RUB"
OSCAR_CURRENCY_FORMAT = {
    "RUB": {
        "currency_digits": False,
        "format_type": "accounting",
        "format": "###0\xa0¤",
    }
}

# Paths
OSCAR_IMAGE_CATEGORIES_FOLDER = "images/categories/%Y/%m/"
OSCAR_IMAGE_PRODUCTS_FOLDER = "images/products/%Y/%m/"
OSCAR_IMAGE_ADDITIONALS_FOLDER = "images/additionals/%Y/%m/"
OSCAR_IMAGE_ACTIONS_FOLDER = "images/actions/%Y/%m/"
OSCAR_IMAGE_PROMOCATEGORIES_FOLDER = "images/promo-categories/%Y/%m/"
OSCAR_IMAGE_OFFERS_FOLDER = "images/offers/%Y/%m/"

# Copy this image from oscar/static/img to your MEDIA_ROOT folder.
# It needs to be there so Sorl can resize it.
OSCAR_MISSING_IMAGE_URL = "image_not_found.jpg"

# Pagination settings
OSCAR_OFFERS_PER_PAGE = 40
OSCAR_PRODUCTS_PER_PAGE = 100
OSCAR_REVIEWS_PER_PAGE = 30
OSCAR_NOTIFICATIONS_PER_PAGE = 30
OSCAR_EMAILS_PER_PAGE = 30
OSCAR_ORDERS_PER_PAGE = 30
OSCAR_ADDRESSES_PER_PAGE = 30
OSCAR_STOCK_ALERTS_PER_PAGE = 30

OSCAR_EVOTOR_ITEMS_PER_PAGE = 40
OSCAR_DASHBOARD_ITEMS_PER_PAGE = 40
OSCAR_DASHBOARD_PAYMENTS_PER_PAGE = 40

# Accounts
OSCAR_ACCOUNTS_REDIRECT_URL = "customer:profile-view"

# Slug handling
OSCAR_SLUG_FUNCTION = "oscar.core.utils.default_slugifier"
OSCAR_SLUG_MAP = {}
OSCAR_SLUG_BLACKLIST = []
OSCAR_SLUG_ALLOW_UNICODE = True

# Cookies
OSCAR_COOKIES_DELETE_ON_LOGOUT = [
    "recently_viewed_products",
]

# Values (using the names of the model constants) from
# "offer.ConditionalOffer.TYPE_CHOICES"
OSCAR_OFFERS_IMPLEMENTED_TYPES = [
    "SITE",
    "VOUCHER",
]

# Menu structure of the dashboard navigation
OSCAR_DASHBOARD_NAVIGATION = [
    {
        "label": "Статистика",
        "icon": "fas fa-line-chart",
        "url_name": "dashboard:index",
    },
    {
        "label": "Каталог",
        "icon": "fas fa-list",
        "children": [
            {
                "label": "Товары",
                "url_name": "dashboard:catalogue-product-list",
            },
            {
                "label": "Категории",
                "url_name": "dashboard:catalogue-category-list",
            },
            {
                "label": "Типы товаров",
                "url_name": "dashboard:catalogue-class-list",
            },
            {
                "label": "Ассортименты",
                "url_name": "dashboard:range-list",
            },
            {
                "label": "Дополнительные товары",
                "url_name": "dashboard:catalogue-additional-list",
            },
            {
                "label": "Опции",
                "url_name": "dashboard:catalogue-option-list",
            },
            {
                "label": "Атрибуты",
                "url_name": "dashboard:catalogue-attribute-list",
            },
            {
                "label": "Группы атрибутов",
                "url_name": "dashboard:catalogue-attribute-option-group-list",
            },
            {
                "label": "Уведомления о наличии",
                "url_name": "dashboard:stock-alert-list",
                "notification": "stock_alerts",
            },
        ],
    },
    {
        "label": "Заказы",
        "icon": "fas fa-shopping-cart",
        "children": [
            {
                "label": "Активные заказы",
                "url_name": "dashboard:order-active-list",
                "notification": "active_orders",
            },
            {
                "label": "Все заказы",
                "url_name": "dashboard:order-list",
                "notification": "all_orders",
            },
            {
                "label": "Статистика",
                "url_name": "dashboard:order-stats",
            },
        ],
    },
    {
        "label": "Магазины",
        "icon": "fas fa-store",
        "children": [
            {
                "label": "Магазины",
                "url_name": "dashboard:store-list",
            },
            {
                "label": "Терминалы",
                "url_name": "dashboard:terminal-list",
            },
            {
                "label": "Группы персонала",
                "url_name": "dashboard:group-list",
            },
            {
                "label": "Персонал",
                "url_name": "dashboard:staff-list",
            },
        ],
    },
    # {
    #     "label": "Доставка",
    #     "icon": "fas fa-delivery",
    #     "children": [
    #         {
    #             "label": "Текущие",
    #             "url_name": "dashboard:delivery-active",
    #             "notification": "delivery_active",
    #         },
    #         {
    #             "label": "Все доставки",
    #             "url_name": "dashboard:delivery-list",
    #         },
    #         {
    #             "label": "Заказы на кухне",
    #             "url_name": "dashboard:delivery-stores",
    #             "notification": "delivery_store",
    #         },
    #         {
    #             "label": "Заказы в доставке",
    #             "url_name": "dashboard:delivery-couriers",
    #             "notification": "delivery_couriers",
    #         },
    #         {
    #             "label": "Статистика",
    #             "url_name": "dashboard:delivery-stats",
    #         },
    #         {
    #             "label": "Зоны доставки",
    #             "url_name": "dashboard:delivery-zones",
    #         },
    #         {
    #             "label": "Курьеры",
    #             "url_name": "dashboard:delivery-couriers-list",
    #         },
    #     ],
    # },
    {
        "label": "ЮKassa",
        "icon": "fas fa-credit-card",
        "children": [
            {
                "label": "Список платежей",
                "url_name": "dashboard:payments-list",
            },
            {
                "label": "Список возвратов",
                "url_name": "dashboard:refunds-list",
            },
        ],
    },
    {
        "label": "Клиенты",
        "icon": "fas fa-users",
        "children": [
            {
                "label": "Клиенты",
                "url_name": "dashboard:customer-list",
            },
            {
                "label": "Отзывы на товары",
                "url_name": "dashboard:reviews-product-list",
                "notification": "feedback_product",
            },
            {
                "label": "Отзывы на заказы",
                "url_name": "dashboard:reviews-order-list",
                "notification": "feedback_order",
            },
        ],
    },
    {
        "label": "Скидки",
        "icon": "fas fa-percent",
        "children": [
            {
                "label": "Предложения",
                "url_name": "dashboard:offer-list",
            },
            {
                "label": "Промокоды",
                "url_name": "dashboard:voucher-list",
            },
            {
                "label": "Наборы промокодов",
                "url_name": "dashboard:voucher-set-list",
            },
        ],
    },
    {
        "label": "Эвотор",
        "icon": "fas fa-evotor",
        "children": [
            {
                "label": "Магазины",
                "url_name": "dashboard:evotor-stores",
            },
            {
                "label": "Терминалы",
                "url_name": "dashboard:evotor-terminals",
            },
            {
                "label": "Персонал",
                "url_name": "dashboard:evotor-staffs",
            },
            {
                "label": "Группы",
                "url_name": "dashboard:evotor-groups",
            },
            {
                "label": "Товары",
                "url_name": "dashboard:evotor-products",
            },
            {
                "label": "Дополнительные товары",
                "url_name": "dashboard:evotor-additionals",
            },
            # {
            #     "label": "Документы",
            #     "url_name": "dashboard:evotor-docs",
            # },
        ],
    },
    # {
    #     "label": "Телеграм",
    #     "icon": "fas fa-telegram",
    #     "children": [
    #         {
    #             "label": "Персонал",
    #             "url_name": "dashboard:telegram-admin",
    #         },
    #         {
    #             "label": "Клиенты",
    #             "url_name": "dashboard:telegram-admin",
    #         },
    #         {
    #             "label": "Сообщения",
    #             "url_name": "dashboard:telegram-errors",
    #         },
    #         {
    #             "label": "Статистика",
    #             "url_name": "dashboard:telegram-errors",
    #         },
    #     ],
    # },
    {
        "label": "Контент",
        "icon": "fas fa-newspaper",
        "children": [
            {
                "label": "Страницы",
                "url_name": "dashboard:page-list",
            },
            # {
            #     "label": "Акции",
            #     "url_name": "dashboard:page-list",
            # },
            # {
            #     "label": "Промо-категории",
            #     "url_name": "dashboard:page-list",
            # },
            # {
            #     "label": "Шаблоны Email",
            #     "url_name": "dashboard:email-list",
            # },
            # {
            #     "label": "Шаблоны SMS",
            #     "url_name": "dashboard:sms-list",
            # },
            # {
            #     "label": "Отправленные СМС",
            #     "url_name": "dashboard:sended-sms",
            # },
        ],
    },
    {
        "label": "Отчеты",
        "icon": "fas fa-chart-bar",
        "url_name": "dashboard:reports-index",
    },
    # {
    #     "label": "Настройки",
    #     "icon": "fas fa-gear",
    #     "children": [
    #         {
    #             "label": "Основные",
    #             "url_name": "dashboard:page-list",
    #         },
    #         {
    #             "label": "Доставка",
    #             "url_name": "dashboard:page-list",
    #         },
    #         {
    #             "label": "Промо-категории",
    #             "url_name": "dashboard:page-list",
    #         },
    #     ],
    # },
]

OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = "oscar.apps.dashboard.nav.default_access_fn"

# Search facets
OSCAR_THUMBNAILER = "oscar.core.thumbnails.SorlThumbnail"
OSCAR_URL_SCHEMA = "http"
OSCAR_SAVE_SENT_EMAILS_TO_DB = True

# Rest settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_METADATA_CLASS": "rest_framework.metadata.SimpleMetadata",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "PAGE_SIZE": 20,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DATETIME_FORMAT": "%s",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

AUTH_USER_MODEL = "user.User"
PHONENUMBER_DEFAULT_REGION = "RU"


# =============
# ORDER
# =============

# Sample order/line status settings. This is quite simplistic. It's like you'll
# want to override the set_status method on the order object to do more
# sophisticated things.
OSCAR_SUCCESS_ORDER_STATUS = "Завершён"
OSCAR_FAIL_ORDER_STATUS = "Отменён"
OSCAR_INITIAL_ORDER_STATUS = "Обрабатывается"
OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS = "Ожидает оплаты"

OSCAR_SUCCESS_LINE_STATUS = "Завершён"
OSCAR_INITIAL_LINE_STATUS = "Обрабатывается"
OSCAR_FAIL_LINE_STATUS = "Отменён"

# Доставка:
# Наличные (Не доделано):
# Обрабатывается  - Готовится - Готов - Доставляется - Завершён

# Безналичные:
# Ожидает оплаты - Оплачен - Готовится - Готов - Доставляется - Завершён

# Самовывоз
# Наличные (Не доделано):
# Ожидает оплаты - Оплачен - Готовится - Готов - Завершён

# Безналичные:
# Ожидает оплаты - Оплачен - Готовится - Готов - Завершён

# This dict defines the new order statuses than an order can move to
OSCAR_ORDER_STATUS_PIPELINE = {
    "Обрабатывается": ("Готовится", "Оплачен", "Завершён", "Отменён"),
    "Ожидает оплаты": ("Оплачен", "Обрабатывается", "Завершён", "Отменён"),
    "Оплачен": ("Готовится", "Завершён", "Отменён"),
    "Готовится": ("Готов", "Завершён", "Отменён"),
    "Готов": ("Доставляется", "Завершён", "Отменён"),
    "Доставляется": ("Завершён", "Отменён"),
    "Завершён": ("Отменён",),
    "Отменён": (),
}

PICKUP_NEXT_STATUS_PIPELINE = {
    "Обрабатывается": "Готовится",
    "Ожидает оплаты": "Оплачен",
    "Оплачен": "Готовится",
    "Готовится": "Готов",
    "Готов": "Завершён",
}

DELIVERY_NEXT_STATUS_PIPELINE = {
    "Обрабатывается": "Готовится",
    "Ожидает оплаты": "Оплачен",
    "Оплачен": "Готовится",
    "Готовится": "Готов",
    "Готов": "Доставляется",
    "Доставляется": "Завершён",
}

OSCAR_LINE_STATUS_PIPELINE = {
    "Обрабатывается": ("Готовится", "Отменён"),
    "Готовится": ("Готов", "Отменён"),
    "Готов": ("Завершён", "Отменён"),
    "Отменён": (),
    "Завершён": (),
}

# This dict defines the line statuses that will be set when an order's status
# is changed
OSCAR_ORDER_STATUS_CASCADE = {
    "Готовится": "Готовится",
    "Готов": "Готов",
    "Завершён": "Завершён",
    "Отменён": "Отменён",
}

ORDER_ACTIVE_STATUSES = (
    "Обрабатывается",
    "Оплачен",
    "Готовится",
    "Готов",
)

ORDER_BUSY_STATUSES = (
    "Ожидает оплаты",
    "Обрабатывается",
    "Оплачен",
    "Готовится",
)

ORDER_FINAL_STATUSES = (
    "Завершён",
    "Отменён",
)

ORDER_STATUS_SEND_TO_EVOTOR = (
    "Обрабатывается",
    "Оплачен",
)

WEBSHOP_PAYMENT_CHOICES = (
    ("YOOMONEY", "Картой Онлайн"),
    ("ELECTRON", "Картой в магазине"),
    ("CASH", "Наличные"),
)

ONLINE_PAYMENTS = ("YOOMONEY",)

OFFLINE_PAYMENTS = (
    "CASH",
    "ELECTRON",
)

CASH_PAYMENTS = ("CASH",)

OFFLINE_ORDERS = ("Эвотор",)

PAYMENT_STATUS = {
    "succeeded": "Успешная оплата",
    "canceled": "Оплата не удалась",
    "pending": "Платеж обрабатвается",
}

REFUND_STATUS = {
    "succeeded": "Успешный возврат",
    "canceled": "Возврат не удался",
    "pending": "Возврат обрабатывается",
}

PAYMENT_ORDER_STATUS = {
    "succeeded": "Оплачен",
    "canceled": "Отменён",
    "pending": "Обрабатывается",
}

REFUND_ORDER_STATUS = {
    "succeeded": "Отменён",
    "canceled": "Оплачен",
    "pending": "Обрабатывается",
}
