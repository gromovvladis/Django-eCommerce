from django.urls import reverse_lazy

HOMEPAGE = reverse_lazy("page:homepage")

# Dynamic class loading
DYNAMIC_CLASS_LOADER = "core.loading.default_class_loader"

DEFAULT_COOKIE_LIFETIME = 7 * 24 * 60 * 60

# Store cookies settings
STORE_COOKIE_LIFETIME = 7 * 24 * 60 * 60

# Basket settings
BASKET_COOKIE_LIFETIME = 7 * 24 * 60 * 60
BASKET_COOKIE_OPEN = "open_basket"
BASKET_COOKIE_SECURE = False
MAX_BASKET_QUANTITY_THRESHOLD = 99

# Recently-viewed products
RECENTLY_VIEWED_COOKIE_LIFETIME = 7 * 24 * 60 * 60
RECENTLY_VIEWED_COOKIE_NAME = "history"
RECENTLY_VIEWED_COOKIE_SECURE = False
RECENTLY_VIEWED_PRODUCTS = 10

# Currency
DEFAULT_CURRENCY = "RUB"
CURRENCY_FORMAT = {
    "RUB": {
        "currency_digits": False,
        "format_type": "accounting",
        "format": "###0\xa0¤",
    }
}

# Paths
IMAGE_CATEGORIES_FOLDER = "images/categories/%Y/%m/"
IMAGE_PRODUCTS_FOLDER = "images/products/%Y/%m/"
IMAGE_ADDITIONALS_FOLDER = "images/additionals/%Y/%m/"
IMAGE_ACTIONS_FOLDER = "images/actions/%Y/%m/"
IMAGE_PROMOCATEGORIES_FOLDER = "images/promo-categories/%Y/%m/"
IMAGE_OFFERS_FOLDER = "images/offers/%Y/%m/"

# Copy this image from /static/img to your MEDIA_ROOT folder.
# It needs to be there so Sorl can resize it.
MISSING_IMAGE_URL = "image_not_found.jpg"

# Pagination settings
OFFERS_PER_PAGE = 40
PRODUCTS_PER_PAGE = 100
REVIEWS_PER_PAGE = 30
NOTIFICATIONS_PER_PAGE = 30
EMAILS_PER_PAGE = 30
ORDERS_PER_PAGE = 30
ADDRESSES_PER_PAGE = 30
STOCK_ALERTS_PER_PAGE = 30

EVOTOR_ITEMS_PER_PAGE = 40
DASHBOARD_ITEMS_PER_PAGE = 40
DASHBOARD_PAYMENTS_PER_PAGE = 40

# Accounts
ACCOUNTS_REDIRECT_URL = "customer:profile-view"

# Slug handling
SLUG_FUNCTION = "core.utils.default_slugifier"
SLUG_MAP = {}
SLUG_BLACKLIST = []
SLUG_ALLOW_UNICODE = True

# Cookies
COOKIES_DELETE_ON_LOGOUT = [
    "recently_viewed_products",
]

# Values (using the names of the model constants) from
# "offer.ConditionalOffer.TYPE_CHOICES"
OFFERS_IMPLEMENTED_TYPES = [
    "SITE",
    "VOUCHER",
]

# Menu structure of the dashboard navigation
DASHBOARD_NAVIGATION = [
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
    #     "icon": "fas fa-shipping",
    #     "children": [
    #         {
    #             "label": "Текущие",
    #             "url_name": "dashboard:shipping-active",
    #             "notification": "shipping_active",
    #         },
    #         {
    #             "label": "Все доставки",
    #             "url_name": "dashboard:shipping-list",
    #         },
    #         {
    #             "label": "Заказы на кухне",
    #             "url_name": "dashboard:shipping-stores",
    #             "notification": "shipping_store",
    #         },
    #         {
    #             "label": "Заказы в доставке",
    #             "url_name": "dashboard:shipping-couriers",
    #             "notification": "shipping_couriers",
    #         },
    #         {
    #             "label": "Статистика",
    #             "url_name": "dashboard:shipping-stats",
    #         },
    #         {
    #             "label": "Зоны доставки",
    #             "url_name": "dashboard:shipping-zones",
    #         },
    #         {
    #             "label": "Курьеры",
    #             "url_name": "dashboard:shipping-couriers-list",
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

DASHBOARD_DEFAULT_ACCESS_FUNCTION = "apps.webshop.dashboard.nav.default_access_fn"

# Search facets
THUMBNAILER = "core.thumbnails.SorlThumbnail"
URL_SCHEMA = "http"
SAVE_SENT_EMAILS_TO_DB = True

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
SUCCESS_ORDER_STATUS = "Завершён"
FAIL_ORDER_STATUS = "Отменён"
INITIAL_ORDER_STATUS = "Обрабатывается"
INITIAL_ONLINE_PAYMENT_ORDER_STATUS = "Ожидает оплаты"

SUCCESS_LINE_STATUS = "Завершён"
INITIAL_LINE_STATUS = "Обрабатывается"
FAIL_LINE_STATUS = "Отменён"

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
ORDER_STATUS_PIPELINE = {
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

LINE_STATUS_PIPELINE = {
    "Обрабатывается": ("Готовится", "Отменён"),
    "Готовится": ("Готов", "Отменён"),
    "Готов": ("Завершён", "Отменён"),
    "Отменён": (),
    "Завершён": (),
}

# This dict defines the line statuses that will be set when an order's status
# is changed
ORDER_STATUS_CASCADE = {
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
