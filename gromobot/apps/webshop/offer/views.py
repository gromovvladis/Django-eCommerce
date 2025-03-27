from core.loading import get_class, get_model
from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, View

ThemeMixin = get_class("webshop.mixins", "ThemeMixin")

ConditionalOffer = get_model("offer", "ConditionalOffer")
Range = get_model("offer", "Range")


class OfferDetailView(ThemeMixin, ListView):
    context_object_name = "products"
    template_name = "offer/detail.html"
    paginate_by = settings.OFFERS_PER_PAGE

    # pylint: disable=W0201
    def get(self, request, *args, **kwargs):
        try:
            self.offer = ConditionalOffer.active.select_related().get(
                slug=self.kwargs["slug"]
            )
        except ConditionalOffer.DoesNotExist:
            raise http.Http404
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["offer"] = self.offer
        ctx["summary"] = "actions"
        ctx["page_title"] = self.offer.name
        ctx["upsell_message"] = self.offer.get_upsell_message(self.request.basket)
        return ctx

    def get_queryset(self):
        """
        Return a queryset of all :py:class:`Product <apps.webshop.catalogue.models.Product>`
        instances related to the :py:class:`ConditionalOffer <apps.offer.models.ConditionalOffer>`.
        """
        return self.offer.products()


class RangeDetailView(ThemeMixin, ListView):
    template_name = "offer/range.html"
    context_object_name = "products"
    paginate_by = settings.PRODUCTS_PER_PAGE

    # pylint: disable=W0201
    def dispatch(self, request, *args, **kwargs):
        self.range = get_object_or_404(Range, slug=kwargs["slug"], is_public=True)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return a queryset of all :py:class:`Product <apps.catalogue.models.Product>`
        instances related to the :py:class:`Range <apps.offer.models.Range>`.
        """
        products = self.range.all_products().browsable()
        return products.order_by("rangeproduct__display_order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["range"] = self.range
        ctx["summary"] = "actions"
        ctx["page_title"] = self.offer.name
        return ctx


class GetUpsellMasseges(ThemeMixin, View):
    template_name = "offer/partials/upsell_message.html"

    def get(self, request, *args, **kwargs):
        try:
            self.offer = ConditionalOffer.active.select_related().get(
                slug=self.kwargs["slug"]
            )
            templates = self.get_template_names()
            upsell_message = render_to_string(
                templates[0],
                {"upsell_message": self.offer.get_upsell_message(request.basket)},
                request=request,
            )

        except ConditionalOffer.DoesNotExist:
            raise http.JsonResponse(
                {"error": "ConditionalOffer.DoesNotExist"}, status=404
            )

        return http.JsonResponse({"upsell_message": upsell_message}, status=202)
