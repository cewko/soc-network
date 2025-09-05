import datetime
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Action


class ActionService:
    DUPLICATE_THRESHOLD_SECONDS = 60
    
    @classmethod
    def create_action(cls, user, verb, target=None):
        if cls._is_duplicate_action(user, verb, target):
            return False
        
        action = Action(user=user, verb=verb, target=target)
        action.save()
        return True
    
    @classmethod
    def _is_duplicate_action(cls, user, verb, target):
        threshold_time = timezone.now() - datetime.timedelta(
            seconds=cls.DUPLICATE_THRESHOLD_SECONDS
        )
        
        queryset = Action.objects.filter(
            user=user,
            verb=verb,
            created__gte=threshold_time
        )
        
        if target:
            target_ct = ContentType.objects.get_for_model(target)
            queryset = queryset.filter(
                target_ct=target_ct,
                target_id=target.id
            )
        else:
            queryset = queryset.filter(target_ct__isnull=True)
        
        return queryset.exists()


def create_action(user, verb, target=None):
    return ActionService.create_action(user, verb, target)