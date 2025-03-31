from core.loading import get_classes, get_model
from django import http
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import ListView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from user_agents import parse

_dir = settings.STATIC_PRIVATE_ROOT

PageTitleMixin, ThemeMixin = get_classes(
    "webshop.mixins", ["PageTitleMixin", "ThemeMixin"]
)

Action = get_model("action", "Action")
PromoCategory = get_model("action", "PromoCategory")


def service_worker(request):
    return HttpResponse(
        open(_dir + "/js/service-worker/service-worker.js", "rb").read(),
        status=202,
        content_type="application/javascript",
    )


class GetCookiesView(APIView):
    """
    Сообщение , что мы используем куки
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        cookies = render_to_string("webshop/includes/cookie.html", request=self.request)
        return http.JsonResponse({"cookies": cookies}, status=202)


class HomePageView(PageTitleMixin, ThemeMixin, ListView):
    """
    Главная страница
    """

    template_name = "homepage/homepage.html"
    context_object_name = "actions"
    summary = "home"

    def get_queryset(self):
        return cache.get_or_set(
            "actions_all",
            lambda: Action.objects.only("image", "slug", "title").filter(
                is_active=True
            ),
            3600,
        )

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["is_mobile"] = self._is_mobile(self.request)

        if not ctx["is_mobile"]:
            ctx["promo_cats"] = cache.get_or_set(
                "promo_cats",
                lambda: PromoCategory.objects.prefetch_related("products").filter(
                    is_active=True
                ),
                3600,
            )

        return ctx

    def _is_mobile(self):
        """Проверяем мобильное ли устройство"""
        agent = parse(self.request.META.get("HTTP_USER_AGENT", ""))
        return agent.is_mobile if agent else False
