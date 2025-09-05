import redis
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .models import Image


class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
    
    def increment_views(self, image_id):
        return self.redis_client.incr(f'image:{image_id}:views')
    
    def increment_ranking(self, image_id):
        return self.redis_client.zincrby("image_ranking", 1, image_id)
    
    def get_top_ranked_images(self, count=10):
        image_ids = self.redis_client.zrange(
            "image_ranking", 0, -1, desc=True
        )[:count]
        return [int(id) for id in image_ids]


class ImageViewService:
    def __init__(self):
        self.redis_service = RedisService()
    
    def record_view(self, image):
        total_views = self.redis_service.increment_views(image.id)
        self.redis_service.increment_ranking(image.id)
        return total_views


class ImageRankingService:
    def __init__(self):
        self.redis_service = RedisService()
    
    def get_most_viewed_images(self, count=10):
        ranking_ids = self.redis_service.get_top_ranked_images(count)
        if not ranking_ids:
            return []
        
        images = list(Image.objects.filter(id__in=ranking_ids))
        return sorted(images, key=lambda x: ranking_ids.index(x.id))


class ImagePaginationService:
    @staticmethod
    def paginate_images(images_queryset, page, per_page=6):
        paginator = Paginator(images_queryset, per_page)
        
        try:
            images_page = paginator.page(page)
            return images_page, False
        except PageNotAnInteger:
            images_page = paginator.page(1)
            return images_page, False
        except EmptyPage:
            images_page = paginator.page(paginator.num_pages)
            return images_page, True
