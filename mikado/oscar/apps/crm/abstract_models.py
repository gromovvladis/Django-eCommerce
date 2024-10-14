import uuid
from django.db import models


class AbstractCRMUser(models.Model):
    user_id = models.CharField(max_length=20, unique=True)
    custom_field = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user_id
    
    class Meta:
        abstract = True


class AbstractCRMToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True, editable=False)
    crm_user = models.OneToOneField("crm.CRMUser", on_delete=models.CASCADE, related_name='token')
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return uuid.uuid4().hex
    
    class Meta:
        abstract = True

