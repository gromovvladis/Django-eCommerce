from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import cached_property
from core.loading import get_class, get_model

BasketLineForm = get_class("webshop.basket.forms", "BasketLineForm")

Line = get_model("basket", "line")


class BaseBasketLineFormSet(BaseModelFormSet):
    def __init__(self, strategy, *args, **kwargs):
        self.strategy = strategy
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super()._construct_form(i, strategy=self.strategy, **kwargs)

    def _should_delete_form(self, form):
        """
        Quantity of zero is treated as if the user checked the DELETE checkbox,
        which results in the basket line being deleted
        """

        if super()._should_delete_form(form):
            return True

        if not form.instance.id:
            return True

    @cached_property
    def forms_with_instances(self):
        return [f for f in self.forms if f.instance.id]

    def __iter__(self):
        """
        Skip forms with removed lines when iterating through the formset.
        """
        return iter(self.forms_with_instances)


BasketLineFormSet = modelformset_factory(
    Line, form=BasketLineForm, formset=BaseBasketLineFormSet, extra=0, can_delete=True
)
