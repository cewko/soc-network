from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ImageQuerySet(models.QuerySet):
    def by_user(self, user):
        return self.filter(user=user)
    
    def liked_by(self, user):
        return self.filter(users_like=user)
    
    def most_liked(self):
        return self.order_by('-total_likes')
    
    def recent(self):
        return self.order_by('-created')


class ImageManager(models.Manager):
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)
    
    def by_user(self, user):
        return self.get_queryset().by_user(user)
    
    def liked_by(self, user):
        return self.get_queryset().liked_by(user)
    
    def most_liked(self):
        return self.get_queryset().most_liked()
    
    def recent(self):
        return self.get_queryset().recent()


class Image(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="images_created",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, blank=True)
    url = models.URLField(max_length=2000)
    image = models.ImageField(upload_to="images/%Y/%m/%d")
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    users_like = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="images_liked",
        blank=True
    )
    total_likes = models.PositiveIntegerField(default=0)
    
    objects = ImageManager()

    class Meta:
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["-total_likes"]),
            models.Index(fields=["user", "-created"]),
        ]
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("images:detail", args=[self.id, self.slug])
    
    def is_liked_by(self, user):
        return self.users_like.filter(id=user.id).exists()
    
    def toggle_like(self, user):
        if self.is_liked_by(user):
            self.users_like.remove(user)
            return False
        else:
            self.users_like.add(user)
            return True