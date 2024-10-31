from django.conf import settings
from django_tables2 import MultiTableMixin
from django.db.models import Case, When, BooleanField, Q
from django.views.generic import TemplateView
from django.utils.encoding import smart_str


class CRMTablesMixin(MultiTableMixin, TemplateView):

    def dispatch(self, request, *args, **kwargs):
        self.queryset = self.get_queryset()
        return super().dispatch(request, *args, **kwargs)
    
    def get_filtered_queryset(self, ids):
        data_list = self.get_queryset()
        return [data_item for data_item in data_list if data_item['evotor_id'] in ids]

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
        evotor_ids = [partner['evotor_id'] for partner in evotor_data]
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
        evotor_ids = [partner['evotor_id'] for partner in self.queryset]
        correct_ids = [partner['evotor_id'] for partner in self.queryset if partner['is_valid'] == True]

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

