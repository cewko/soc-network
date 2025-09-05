from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ActionQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)
    
    def recent(self):
        return self.order_by('-created')
    
    def with_target_type(self, model_class):
        content_type = ContentType.objects.get_for_model(model_class)
        return self.filter(target_ct=content_type)


class ActionManager(models.Manager):
    def get_queryset(self):
        return ActionQuerySet(self.model, using=self._db)
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def recent(self):
        return self.get_queryset().recent()
    
    def with_target_type(self, model_class):
        return self.get_queryset().with_target_type(model_class)


class Action(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actions",
        on_delete=models.CASCADE
    )
    verb = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True)
    target_ct = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        related_name="target_obj",
        on_delete=models.CASCADE
    )
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("target_ct", "target_id")

    objects = ActionManager()

    class Meta:
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["target_ct", "target_id"]),
            models.Index(fields=["user", "-created"])
        ]
        ordering = ["-created"]

    def __str__(self):
        return f'{self.user} {self.verb} {self.target or ""}'
