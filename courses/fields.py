from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class OrderField(models.PositiveIntegerField):

    def __init__(self, for_fields=None, *args, **kwargs):
        self.for_fields = for_fields
        super(OrderField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:
            # no current value
            try:
                qs = self.model.objects.all()
                if self.for_fields:
                    # filter by objects with the same field values
                    # for the fields in 'for_fields'
                    query = {field: getattr(model_instance, field) for field in self.for_fields}
                    # This will filter the ones with the same `for_fields` attributes in the query set
                    # If run from the 'Module' class will return the queryset with the same courses among the 'Module' instances
                    qs = qs.filter(**query)
                # the statement below throws the exception ObjectDoesNotExist
                last_item = qs.latest(self.attname)
                value = last_item.order + 1
            except ObjectDoesNotExist:
                value = 0
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(OrderField, self).pre_save(model_instance, add)
