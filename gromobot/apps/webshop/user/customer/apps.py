from core.application import Config
from core.loading import get_class
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views import generic


class CustomerConfig(Config):
    label = "customer"
    name = "apps.webshop.user.customer"
    verbose_name = "Клиент"

    namespace = "customer"

    # pylint: disable=attribute-defined-outside-init, reimported, unused-import
    def ready(self):
        from . import receivers

        self.summary_view = get_class(
            "webshop.user.customer.views", "AccountSummaryView"
        )
        self.order_history_view = get_class(
            "webshop.user.customer.views", "OrderHistoryView"
        )
        self.order_detail_view = get_class(
            "webshop.user.customer.views", "OrderDetailView"
        )

        # self.order_line_view = get_class("webshop.user.customer.views", "OrderLineView")

        self.address_list_view = get_class(
            "webshop.user.customer.views", "AddressListView"
        )
        self.address_create_view = get_class(
            "webshop.user.customer.views", "AddressCreateView"
        )
        self.address_update_view = get_class(
            "webshop.user.customer.views", "AddressUpdateView"
        )
        self.address_delete_view = get_class(
            "webshop.user.customer.views", "AddressDeleteView"
        )

        self.login_view = get_class("webshop.user.customer.views", "AccountAuthView")
        self.login_api_view = get_class(
            "webshop.user.customer.views", "AccountAuthModalView"
        )
        self.logout_view = get_class("webshop.user.customer.views", "LogoutView")

        self.profile_view = get_class("webshop.user.customer.views", "ProfileView")
        # self.profile_update_view = get_class("webshop.user.customer.views", "ProfileUpdateView")
        # self.profile_delete_view = get_class("webshop.user.customer.views", "ProfileDeleteView")
        # self.change_password_view = get_class("webshop.user.customer.views", "ChangePasswordView")

        self.notification_inbox_view = get_class(
            "webshop.communication.notifications.views", "InboxView"
        )
        self.notification_archive_view = get_class(
            "webshop.communication.notifications.views", "ArchiveView"
        )
        self.notification_update_view = get_class(
            "webshop.communication.notifications.views", "UpdateView"
        )
        self.notification_detail_view = get_class(
            "webshop.communication.notifications.views", "DetailView"
        )

        self.wishlists_add_product_view = get_class(
            "webshop.user.customer.wishlists.views", "WishListAddProduct"
        )
        self.wishlists_detail_view = get_class(
            "webshop.user.customer.wishlists.views", "WishListDetailView"
        )
        self.wishlists_remove_product_view = get_class(
            "webshop.user.customer.wishlists.views", "WishListRemoveProduct"
        )

    def get_urls(self):
        urls = [
            # Login, logout and register doesn't require login
            path("login/", self.login_view.as_view(), name="login"),
            path("api/login/", self.login_api_view.as_view(), name="api-login"),
            path("logout/", self.logout_view.as_view(), name="logout"),
            path("", login_required(self.summary_view.as_view()), name="summary"),
            # Profile
            path(
                "profile/",
                login_required(self.profile_view.as_view()),
                name="profile-view",
            ),
            # Order history
            path(
                "orders/",
                login_required(self.order_history_view.as_view()),
                name="order-list",
            ),
            path(
                "orders/<str:order_number>/",
                login_required(self.order_detail_view.as_view()),
                name="order",
            ),
            # Address book
            path(
                "address/",
                login_required(self.address_list_view.as_view()),
                name="address-list",
            ),
            path(
                "address/add/",
                login_required(self.address_create_view.as_view()),
                name="address-create",
            ),
            path(
                "address/<int:pk>/",
                login_required(self.address_update_view.as_view()),
                name="address-detail",
            ),
            path(
                "address/<int:pk>/delete/",
                login_required(self.address_delete_view.as_view()),
                name="address-delete",
            ),
            # Notifications
            # Redirect to notification inbox
            path(
                "notifications/",
                generic.RedirectView.as_view(
                    url="/accounts/notifications/inbox/", permanent=False
                ),
            ),
            path(
                "notifications/inbox/",
                login_required(self.notification_inbox_view.as_view()),
                name="notifications-inbox",
            ),
            path(
                "notifications/archive/",
                login_required(self.notification_archive_view.as_view()),
                name="notifications-archive",
            ),
            path(
                "notifications/update/",
                login_required(self.notification_update_view.as_view()),
                name="notifications-update",
            ),
            path(
                "notifications/<int:pk>/",
                login_required(self.notification_detail_view.as_view()),
                name="notifications-detail",
            ),
            # Wishlists
            path(
                "wishlist/",
                login_required(self.wishlists_detail_view.as_view()),
                name="wishlist",
            ),
            path(
                "wishlist/add/<int:product_pk>/",
                login_required(self.wishlists_add_product_view.as_view()),
                name="wishlist-add-product",
            ),
            path(
                "wishlist/<str:key>/",
                self.wishlists_detail_view.as_view(),
                name="wishlist-detail",
            ),
            path(
                "wishlist/remove/<int:product_pk>/",
                login_required(self.wishlists_remove_product_view.as_view()),
                name="wishlist-remove-product",
            ),
        ]

        return self.post_process_urls(urls)
