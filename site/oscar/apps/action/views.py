from django.conf import settings
from django.http import Http404
from django.views.generic import ListView, DetailView
from django.db.models import Count
from django.core.cache import cache

from oscar.views import sort_queryset
from oscar.core.loading import get_model, get_class

PageTitleMixin = get_class("customer.mixins", "PageTitleMixin")

ConditionalOffer = get_model("offer", "ConditionalOffer")
Action = get_model("action", "Action")
PromoCategory = get_model("action", "PromoCategory")


class ActionsListView(PageTitleMixin, ListView):
    model = ConditionalOffer
    context_object_name = "offers"
    template_name = "oscar/action/action_list.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    page_title = "Акции"

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
        actions = cache.get("actions_all")

        if not actions:
            actions = Action.objects.prefetch_related("products").filter(
                is_active=True
            )
            cache.set("actions_all", actions, 3600)

        ctx["actions"] = actions
        ctx["summary"] = "actions"
        return ctx


class PromoDetailMixin(DetailView):
    template_name = "oscar/action/action_detail.html"
    context_object_name = "action"

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

    def is_viewable(self, action, request):
        return action.is_active or request.user.is_staff

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, "object"):
            return self.object
        else:
            self.kwargs["slug"] = self.kwargs.get("action_slug")
            return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["summary"] = "actions"
        ctx["page_title"] = self.object.title
        return ctx


class ActionDetailView(PromoDetailMixin):
    model = Action


class PromoCatDetailView(PromoDetailMixin):
    model = PromoCategory
