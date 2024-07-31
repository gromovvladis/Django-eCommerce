from django.urls import reverse_lazy
from yookassa import Configuration


OSCAR_SHOP_NAME = "Микадо Красноярск"
OSCAR_HOMEPAGE = reverse_lazy("home:index")

# Dynamic class loading
OSCAR_DYNAMIC_CLASS_LOADER = "oscar.core.loading.default_class_loader"

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
    'RUB': {
        'currency_digits': False,
        'format_type': "accounting",
        'format': '###0\xa0¤',
    } 
}

# Paths
OSCAR_IMAGE_FOLDER = "images/products/%Y/%m/"
OSCAR_DELETE_IMAGE_FILES = True

# Copy this image from oscar/static/img to your MEDIA_ROOT folder.
# It needs to be there so Sorl can resize it.
OSCAR_MISSING_IMAGE_URL = "image_not_found.jpg"

# Address settings
# OSCAR_REQUIRED_ADDRESS_FIELDS = (
#     "line1",
#     "line2",
# )

# Pagination settings

OSCAR_OFFERS_PER_PAGE = 20
OSCAR_PRODUCTS_PER_PAGE = 20
OSCAR_REVIEWS_PER_PAGE = 20
OSCAR_NOTIFICATIONS_PER_PAGE = 20
OSCAR_EMAILS_PER_PAGE = 20
OSCAR_ORDERS_PER_PAGE = 20
OSCAR_ADDRESSES_PER_PAGE = 20
OSCAR_STOCK_ALERTS_PER_PAGE = 20
OSCAR_DASHBOARD_ITEMS_PER_PAGE = 40
OSCAR_DASHBOARD_PAYMENTS_PER_PAGE = 40

# Reviews
OSCAR_MODERATE_REVIEWS = False

# Accounts
OSCAR_ACCOUNTS_REDIRECT_URL = "customer:profile-view"

# Registration
EMAIL_SUBJECT_PREFIX = 'Mikado'
OSCAR_FROM_EMAIL = "info@mikado-sushi.ru"
OSCAR_SEND_ORDER_PLACED_EMAIL = False
OSCAR_SEND_REGISTRATION_EMAIL = False

# Email
# EMAIL_USER=
# EMAIL_PASSWORD=

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

# Hidden Oscar features, e.g. wishlists or reviews
OSCAR_HIDDEN_FEATURES = []

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
                "label": "Продукты",
                "url_name": "dashboard:catalogue-product-list",
            },
            {
                "label": "Категории",
                "url_name": "dashboard:catalogue-category-list",
            },
            {
                "label": "Типы продуктов",
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
                "label": "Группы параметров атрибутов",
                "url_name": "dashboard:catalogue-attribute-option-group-list",
            },
            {
                "label": "Оповещения о малых остатках",
                "url_name": "dashboard:stock-alert-list",
            },
        ],
    },
    {
        "label": "Заказы",
        "icon": "fas fa-shopping-cart",
        "children": [
            # {
            #     "label": "Активные заказы",
            #     "url_name": "dashboard:order-active-list",
            # },
            {
                "label": "Все заказы",
                "url_name": "dashboard:order-list",
            },
            {
                "label": "Статистика",
                "url_name": "dashboard:order-stats",
            },
            {
                "label": "Точки продажи",
                "url_name": "dashboard:partner-list",
            },
        ],
    },
    {
        "label": "Клиенты",
        "icon": "fas fa-users",
        "children": [
            {
                "label": "Клиенты",
                "url_name": "dashboard:users-index",
            },
            # {
            #     "label": "Персонал",
            #     "url_name": "dashboard:staff-index",
            # },
            # {
            #     "label": "SMS Aero",
            #     "url_name": "dashboard:sms-aero",
            # },
            # {
            #     "label": "Отправленные СМС",
            #     "url_name": "dashboard:sended-sms",
            # },
        ],
    },
    {
        "label": "Скидки",
        "icon": "fas fa-bullhorn",
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
        "label": "Контент",
        "icon": "fas fa-folder",
        "children": [
            {
                "label": "Страницы",
                "url_name": "dashboard:page-list",
            },
            {
                "label": "Шаблоны Email",
                "url_name": "dashboard:comms-list",
            },
            {
                "label": "Шаблоны SMS",
                "url_name": "dashboard:comms-list",
            },
            {
                "label": "Отзывы к товарам",
                "url_name": "dashboard:reviews-list",
            },
            # {
            #     "label": "Отзывы к заказам",
            #     "url_name": "dashboard:reviews-orders-list",
            # },
        ],
    },
    {
        "label": "Оплата",
        "icon": "fas fa-money-bill-transfer",
        "children": [
            {
                "label": "Список платежей",
                "url_name": "dashboard:payments-list",
            },
            {
                "label": "Список возвратов",
                "url_name": "dashboard:refunds-list",
            },
        ]
    },
    {
        "label": "Доставка",
        "icon": "fas fa-delivery",
        "children": [
            {
                "label": "Статистика",
                "url_name": "dashboard:delivery-stats",
            },
            {
                "label": "Карта",
                "url_name": "dashboard:delivery-map",
            },
            {
                "label": "Зоны доставки",
                "url_name": "dashboard:delivery-zones",
            },
            {
                "label": "Курьеры",
                "url_name": "dashboard:delivery-couriers-list",
            },
            {
                "label": "Заказы на кухне",
                "url_name": "dashboard:delivery-kitchen",
            },
            {
                "label": "Заказы в доставке",
                "url_name": "dashboard:delivery-couriers",
            },
        ],
    },
    {
        "label": "Tillypad",
        "icon": "fas fa-tillypad",
        "children": [
            {
                "label": "Отправленные заказы",
                "url_name": "dashboard:crm-orders",
            },
            {
                "label": "Стоп-лист",
                "url_name": "dashboard:crm-stop-list",
            },
            {
                "label": "Прейскурант",
                "url_name": "dashboard:crm-price-list",
            },
            {
                "label": "Курьеры",
                "url_name": "dashboard:crm-couriers",
            },
            {
                "label": "Доставки",
                "url_name": "dashboard:crm-delivery",
            },
        ],
    },
    {
        "label": "Телеграм",
        "icon": "fas fa-telegram",
        "children": [
            {
                "label": "Aдмин",
                "url_name": "dashboard:telegram-admin",
            },
            {
                "label": "Oшибки",
                "url_name": "dashboard:telegram-errors",
            },
            {
                "label": "Курьеры",
                "url_name": "dashboard:telegram-couriers",
            },
        ],
    },
    {
        "label": "Отчеты",
        "icon": "fas fa-chart-bar",
        "url_name": "dashboard:reports-index",
    },
]
OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = "oscar.apps.dashboard.nav.default_access_fn"

# Search facets

OSCAR_THUMBNAILER = "oscar.core.thumbnails.SorlThumbnail"

OSCAR_URL_SCHEMA = "http"

OSCAR_SAVE_SENT_EMAILS_TO_DB = True


#rest settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
    ),

    'DEFAULT_PARSER_CLASSES': (
        #'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DATETIME_FORMAT': '%s',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}


AUTH_USER_MODEL = 'user.User'
PHONENUMBER_DEFAULT_REGION = 'RU'


SMS_AUTH_SETTINGS = {
    "SMS_CELERY_FILE_NAME": "run_celery",
    "SMS_AUTH_PROVIDER_FROM": "Mikado",
    "SMS_AUTH_MESSAGE": "Код для входа на сайт:",
    "SMS_DEBUG_CODE": 1111,
    "SMS_AUTH_PROVIDER_URL": "https://gate.smsaero.ru/v2",
    "SMS_USER_SERIALIZER": "api.serializers.DefaultUserSerializer",
}

# Order processing
# ================

# Sample order/line status settings. This is quite simplistic. It's like you'll
# want to override the set_status method on the order object to do more
# sophisticated things.
OSCAR_INITIAL_ORDER_STATUS = 'Обрабатывается'
OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS = 'Ожидает оплаты'
OSCAR_PAID_ONLINE_PAYMENT_ORDER_STATUS = 'Оплачен'
OSCAR_INITIAL_LINE_STATUS = 'Новый заказ'

# This dict defines the new order statuses than an order can move to
OSCAR_ORDER_STATUS_PIPELINE = {
    'Ожидает оплаты': ('Оплачен', 'Отменен'), 
    'Оплачен': ('Готовится', 'Отменен'),
    'Обрабатывается': ('Оплачен', 'Готовится', 'Отменен'),
    'Готовится': ('Готов', 'Отменен'),
    'Готов': ('Доставляется', 'Завершен', 'Отменен'),
    'Доставляется': ('Завершен', 'Отменен'),
    'Отменен': (),
    'Завершен': (),
}

# This dict defines the line statuses that will be set when an order's status
# is changed
OSCAR_ORDER_STATUS_CASCADE = {
    'Обрабатывается': 'Ожидание',
    'Готовится': 'Готовится',
    'Готов': 'Готов',
    'Завершен': 'Доставлен',
    'Отменен': 'Отменен',
}

# Payment
# ====

# PAYMENT_SUCCESS_URL=
# PAYMENT_CANCEL_URL=

# Payment choices
WEBSHOP_PAYMENT_CHOICES = (
    ('SBP', 'Yoomoney'),
    ('CARD', 'Карта'),
    ('CASH', 'Наличными курьеру при получении'),
    ('COURIER-CARD', 'Картой курьеру при получении'),
)

ONLINE_PAYMENTS = [
    'CARD',
    'SBP',
]

OFFLINE_PAYMENTS = [
    'CASH',
    'COURIER-CARD',
]

CASH_PAYMENTS = [
    'CASH',
]

PAYMENT_STATUS = {
    'succeeded': 'Успешная оплата',
    'canceled': 'Оплата не удалась',
    'pending': 'Платеж обрабатвается',
}

REFUND_STATUS = {
    'succeeded': 'Успешный возврат',
    'canceled': 'Возврат не удался',
    'pending': 'Возврат обрабатывается',
}

PAYMENT_ORDER_STATUS = {
    'succeeded': 'Оплачен',
    'canceled': 'Отменен',
    'pending': 'Обрабатывается',
}

REFUND_ORDER_STATUS = {
    'succeeded': 'Отменен',
    'canceled': 'Оплачен',
    'pending': 'Обрабатывается',
}