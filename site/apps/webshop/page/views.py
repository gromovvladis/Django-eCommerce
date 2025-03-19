from django import http
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import ListView
from core.loading import get_class, get_model, get_classes
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

    def get_queryset(self):
        actions = cache.get("actions_all")
        if not actions:
            actions = Action.objects.only("image", "slug", "title").filter(
                is_active=True
            )
            cache.set("actions_all", actions, 3600)

        return actions

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        agent = parse(self.request.META["HTTP_USER_AGENT"])
        ctx["is_mobile"] = agent.is_mobile if agent else False
        ctx["summary"] = "home"

        if not agent.is_mobile:
            promo_cats = cache.get("promo_cats")
            if not promo_cats:
                promo_cats = PromoCategory.objects.prefetch_related("products").filter(
                    is_active=True
                )
                cache.set("promo_cats", promo_cats, 3600)

            ctx["promo_cats"] = promo_cats

        return ctx
