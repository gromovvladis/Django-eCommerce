from user_agents import parse

from django import http
from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.generic import  ListView, DetailView
from django.db.models import Count
from django.core.cache import cache
from django.template.loader import render_to_string

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from oscar.views import sort_queryset
from oscar.core.loading import get_model

_dir = settings.STATIC_PRIVATE_ROOT

ConditionalOffer = get_model("offer", "ConditionalOffer")
Action = get_model("home", "Action")
PromoCategory = get_model("home", "PromoCategory")

def service_worker(request):
    return HttpResponse(open(_dir + '/js/dashboard/utils/service-worker.js', 'rb').read(), status=202, content_type='application/javascript')


class GetCookiesView(APIView):
    """
    Сообщение , что мы используем куки
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        cookies = render_to_string("oscar/includes/cookie.html", request=self.request)
        return http.JsonResponse({"cookies": cookies}, status = 202)
  

class HomeView(ListView):
    """
    Главная страница
    """
    template_name = "oscar/home/homepage.html"

    def get_queryset(self):

        actions = cache.get('actions_all')

        if not actions:
            actions = Action.objects.only('image', 'slug', 'title').filter(is_active=True)
            cache.set("actions_all", actions, 3600)

        return actions

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["summary"] = settings.PRIMARY_TITLE
        
        agent = parse(self.request.META['HTTP_USER_AGENT'])
        ctx["is_mobile"] = agent.is_mobile

        if not agent.is_mobile:
            promo_cats = cache.get('promo_cats_all')
            if not promo_cats:
                promo_cats = PromoCategory.objects.prefetch_related('products_related').filter(is_active=True)
                cache.set("promo_cats_all", promo_cats, 3600)

            ctx["promo_cats"] = promo_cats

        return ctx


class ActionsView(ListView):
    model = ConditionalOffer
    context_object_name = "offers"
    template_name = "oscar/home/actions/actions.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):

        qs = self.model._default_manager.annotate(
            voucher_count=Count("vouchers")
        ).select_related("benefit", "condition")
        qs = sort_queryset(
            qs,
            self.request,
            [
                "name",
                "offer_type",
                "start_datetime",
                "end_datetime",
                "num_applications",
                "total_discount",
            ],
        )

        return qs
    

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        actions = cache.get('actions_all')

        if not actions:
            actions = Action.objects.prefetch_related('products_related').filter(is_active=True)
            cache.set("actions_all", actions, 3600)

        ctx["actions"] = actions
        ctx["summary"] = "Акции"
        return ctx


class PromoDetailView(DetailView):
    template_name = "oscar/home/actions/detail.html"
    context_object_name = "action"
    model = Action
    template_folder = "home"

    def get(self, request, *args, **kwargs):
        """
        Ensures that the correct URL is used before rendering a response
        """
        # pylint: disable=attribute-defined-outside-init
        self.object = action = self.get_object()

        # Do allow staff members so they can test layout etc.
        if not self.is_viewable(action, request):
            raise Http404()

        response = super().get(request, *args, **kwargs)
        # self.send_signal(request, response, product)
        return response

    def is_viewable(self, product, request):
        return product.is_active or request.user.is_staff

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, "object"):
            return self.object
        else:
            self.kwargs["slug"] = self.kwargs.get("action_slug")
            return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["summary"] = self.object.title
        return ctx
    

class ActionDetailView(PromoDetailView):
    model = Action


class PromoCatDetailView(PromoDetailView):
    model = PromoCategory
