from django.conf import settings
from django_tables2 import MultiTableMixin, SingleTableView
from django.db.models import Case, When, BooleanField, Q
from django.views.generic import TemplateView
from django.utils.encoding import smart_str
from django.contrib import messages
from django.shortcuts import redirect
import logging

logger = logging.getLogger("oscar.dashboard")

class CRMTablesMixin(MultiTableMixin, TemplateView):

    def redirect_with_get_params(self, url, request):
        """
        Перенаправляет на указанный URL, сохраняя GET-параметры из запроса.
        """
        url += "?" + request.GET.urlencode()
        return redirect(url)
        
    def dispatch(self, request, *args, **kwargs):
        self.queryset = self.get_queryset()
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        delete_invalid = request.POST.get("delete_invalid", 'False')
        if delete_invalid == 'True':    
            return self.delete_models(True)

        delete_selected = request.POST.get("delete_selected", 'False')
        if delete_selected == 'True':    
            return self.delete_models(False)
        
        update_all = request.POST.get("update_all", 'False')
        if update_all == 'True':
            return self.update_models(self.queryset, False)
        
        ids = request.POST.getlist("selected_%s" % self.get_checkbox_object_name())
        ids = [id for id in map(str, ids) if id.strip()]
        if not ids:
            messages.error(
                self.request,
                ("Вам нужно выбрать хотя бы одну позицую для обновления"),
            )
            return self.redirect_with_get_params(self.url_redirect, request)

        qs = self.get_filtered_queryset(ids)
        return self.update_models(qs, True)

    def delete_models(self, delete_invalid):
        try:
            if delete_invalid:
                correct_ids = [model_qs['id'] for model_qs in self.queryset if model_qs['is_valid'] == True]
                self.model.objects.exclude(evotor_id__in=correct_ids).delete()
            else:
                ids = self.request.POST.getlist("selected_%s" % self.get_checkbox_object_name())
                self.model.objects.filter(id__in=ids).delete()
        except Exception as e:
            logger.error("Ошибка при удалении моделей из бд на странице CRM - %s" % str(e))
            messages.error(
                self.request,
                ("Записи на сайте не были удалены!"),
            )
            self.redirect_with_get_params(self.url_redirect, self.request)
            # return redirect(self.url_redirect) 
               
        messages.success(
            self.request,
            ("Записи на сайте были успешно удалены"),
        )
        return self.redirect_with_get_params(self.url_redirect, self.request)
        # return redirect(self.url_redirect)

    def get_filtered_queryset(self, ids):
        data_list = self.get_queryset()
        return [data_item for data_item in data_list if data_item['id'] in ids]

    def get_checkbox_object_name(self):
        return smart_str(self.model._meta.object_name.lower())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        stauses = self.get_evotor_statuses()
        ctx['is_valid'] = stauses['is_valid']
        ctx['not_is_valid'] = stauses['not_is_valid'] 
        ctx['not_evotor_id'] = stauses['not_evotor_id'] 
        ctx['wrong_evotor_id'] = stauses['wrong_evotor_id']
        return ctx
    
    def get_evotor_statuses(self):
        stauses = {}
        evotor_data = self.queryset
        stauses['is_valid'] = sum(1 for item in evotor_data if item.get('is_valid') is True)
        stauses['not_is_valid'] = sum(1 for item in evotor_data if item.get('is_valid') is False and item.get('is_created'))
        evotor_ids = [model_evator['id'] for model_evator in evotor_data]
        models = self.model.objects.all()
        stauses['not_evotor_id'] = models.filter(evotor_id__isnull=True).count()
        stauses['wrong_evotor_id'] = models.filter(evotor_id__isnull=False).exclude(evotor_id__in=evotor_ids).count()
        return stauses

    def get_tables(self):
        return [
            self.get_evotor_table(),
            self.get_site_table(),
        ]

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_EVOTOR_ITEMS_PER_PAGE)

    def get_evotor_table(self):
        return self.table_evotor(self.queryset)

    def get_site_table(self):
        evotor_ids = [model_qs['id'] for model_qs in self.queryset]
        correct_ids = [model_qs['id'] for model_qs in self.queryset if model_qs['is_valid'] == True]

        site_models = self.model.objects.annotate(
            is_valid=Case(
                When(Q(evotor_id__in=evotor_ids) & Q(evotor_id__in=correct_ids), then=True),
                default=False,
                output_field=BooleanField()
            ),
            wrong_evotor_id=Case(
                When(
                    Q(evotor_id__isnull=False) & ~Q(evotor_id__in=evotor_ids),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).order_by(
            '-wrong_evotor_id',
            'is_valid',
            'evotor_id',
            '-is_valid'
        )
            
        return self.table_site(site_models)


class CRMTableMixin(SingleTableView):

    def post(self, request, *args, **kwargs):
        delete_invalid = request.POST.get("delete_invalid", 'False')
        if delete_invalid == 'True':    
            return self.delete_models(True)

        delete_selected = request.POST.get("delete_selected", 'False')
        if delete_selected == 'True':    
            return self.delete_models(False)
        
        update_all = request.POST.get("update_all", 'False')
        if update_all == 'True':
            return self.update_models(self.queryset, False)
        
        ids = request.POST.getlist("selected_%s" % self.get_checkbox_object_name())
        ids = [id for id in map(str, ids) if id.strip()]
        if not ids:
            messages.error(
                self.request,
                ("Вам нужно выбрать хотя бы одну позицую для обновления"),
            )
            return self.redirect_with_get_params(self.url_redirect, request)
            # return redirect(self.url_redirect)

        qs = self.get_filtered_queryset(ids)
        return self.update_models(qs, True)

    def get_filtered_queryset(self, ids):
        data_list = self.get_queryset()
        return [data_item for data_item in data_list if data_item['id'] in ids]

    def get_checkbox_object_name(self):
        return smart_str(self.model._meta.object_name.lower())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        stauses = self.get_evotor_statuses()
        ctx['is_valid'] = stauses['is_valid']
        ctx['not_is_valid'] = stauses['not_is_valid'] 
        ctx['not_evotor_id'] = stauses['not_evotor_id'] 
        ctx['wrong_evotor_id'] = stauses['wrong_evotor_id']
        return ctx
    
    def get_evotor_statuses(self):
        stauses = {}
        evotor_data = self.queryset
        stauses['is_valid'] = sum(1 for item in evotor_data if item.get('is_valid') is True)
        stauses['not_is_valid'] = sum(1 for item in evotor_data if item.get('is_valid') is False and item.get('is_created'))
        evotor_ids = [model_evator['id'] for model_evator in evotor_data]
        models = self.model.objects.all()
        stauses['not_evotor_id'] = models.filter(evotor_id__isnull=True).count()
        stauses['wrong_evotor_id'] = models.filter(evotor_id__isnull=False).exclude(evotor_id__in=evotor_ids).count()
        return stauses

    # def get_table_pagination(self, table):
    #     return dict(per_page=settings.OSCAR_EVOTOR_ITEMS_PER_PAGE)

    def get_evotor_table(self):
        return self.table_evotor(self.queryset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        access = ["user.full_access", "catalogue.full_access", "catalogue.update_stockrecord"]
        ctx["product_access"] = any(self.request.user.has_perm(perm) for perm in access)
        return ctx
    
    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)

        if "status" in self.request.GET:
            self.form = StockAlertSearchForm(self.request.GET)
            if self.form.is_valid():
                status = self.form.cleaned_data["status"]
                table.caption = 'Уведомление со статусом "%s"' % status
        else:
            self.form = StockAlertSearchForm()

        return table

    # def get_queryset(self):
#         if "status" in self.request.GET:
#             self.form = StockAlertSearchForm(self.request.GET)
#             if self.form.is_valid():
#                 status = self.form.cleaned_data["status"]
#                 return StockAlert.objects.filter(status=status).select_related("stockrecord").annotate(
#                 name=F("stockrecord__product__title"),
#                 partner=F("stockrecord__partner__name"),
#                 threshold=F("stockrecord__low_stock_threshold"),
#                 num_in_stock=F("stockrecord__num_in_stock"),
#                 num_allocated=F("stockrecord__num_allocated"),
#             )       
#         else:
#             return StockAlert.objects.all().select_related("stockrecord").annotate(
#                 name=F("stockrecord__product__title"),
#                 partner=F("stockrecord__partner__name"),
#                 threshold=F("stockrecord__low_stock_threshold"),
#                 num_in_stock=F("stockrecord__num_in_stock"),
#                 num_allocated=F("stockrecord__num_allocated"),
#             )
