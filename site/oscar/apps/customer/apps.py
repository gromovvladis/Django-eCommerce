from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views import generic

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CustomerConfig(OscarConfig):
    label = "customer"
    name = "oscar.apps.customer"
    verbose_name = "Клиент"

    namespace = "customer"

    # pylint: disable=attribute-defined-outside-init, reimported, unused-import
    def ready(self):
        from . import receivers
        from .alerts import receivers

        self.summary_view = get_class("customer.views", "AccountSummaryView")
        self.order_history_view = get_class("customer.views", "OrderHistoryView")
        self.order_detail_view = get_class("customer.views", "OrderDetailView")

        # self.order_line_view = get_class("customer.views", "OrderLineView")

        self.address_list_view = get_class("customer.views", "AddressListView")
        self.address_create_view = get_class("customer.views", "AddressCreateView")
        self.address_update_view = get_class("customer.views", "AddressUpdateView")
        self.address_delete_view = get_class("customer.views", "AddressDeleteView")

        self.login_view = get_class("customer.views", "AccountAuthView")
        self.login_api_view = get_class("customer.views", "AccountAuthModalView")
        self.logout_view = get_class("customer.views", "LogoutView")

        self.profile_view = get_class("customer.views", "ProfileView")
        # self.profile_update_view = get_class("customer.views", "ProfileUpdateView")
        # self.profile_delete_view = get_class("customer.views", "ProfileDeleteView")
        # self.change_password_view = get_class("customer.views", "ChangePasswordView")

        self.notification_inbox_view = get_class("communication.notifications.views", "InboxView")
        self.notification_archive_view = get_class("communication.notifications.views", "ArchiveView")
        self.notification_update_view = get_class("communication.notifications.views", "UpdateView")
        self.notification_detail_view = get_class("communication.notifications.views", "DetailView")

        self.wishlists_add_product_view = get_class("customer.wishlists.views", "WishListAddProduct")
        self.wishlists_detail_view = get_class("customer.wishlists.views", "WishListDetailView")
        self.wishlists_remove_product_view = get_class("customer.wishlists.views", "WishListRemoveProduct")

        self.feedbacks_available_view = get_class("customer.feedbacks.views", "OrderFeedbackAvailibleListView")
        self.feedbacks_view = get_class("customer.feedbacks.views", "OrderFeedbackListView")
        self.feedbacks_add_view = get_class("customer.feedbacks.views", "AddOrderFeedbackView")

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
                "addresses/",
                login_required(self.address_list_view.as_view()),
                name="address-list",
            ),
            path(
                "addresses/add/",
                login_required(self.address_create_view.as_view()),
                name="address-create",
            ),
            path(
                "addresses/<int:pk>/",
                login_required(self.address_update_view.as_view()),
                name="address-detail",
            ),
            path(
                "addresses/<int:pk>/delete/",
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
            # feedback
            path(
                "feedbacks/",
                login_required(self.feedbacks_view.as_view()),
                name="feedbacks",
            ),
            path(
                "feedbacks/add/",
                login_required(self.feedbacks_available_view.as_view()),
                name="feedbacks-available",
            ),
            path(
                "feedbacks/add/<int:order_number>/",
                login_required(self.feedbacks_add_view.as_view()),
                name="feedback-add",
            ),
        ]

        return self.post_process_urls(urls)
