from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(
        upload_to='users/%Y/%m/%d/',
        blank=True,
        default='users/default_profile_picture.png'
    )
    biography = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Profile of {self.user.username}'

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'.strip() or self.user.username


class Contact(models.Model):
    user_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='rel_from_set',
        on_delete=models.CASCADE
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='rel_to_set',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_from', 'user_to'],
                name='unique_contact'
            ),
            models.CheckConstraint(
                check=~models.Q(user_from=models.F('user_to')),
                name='no_self_follow'
            ),
        ]
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['user_from']),
            models.Index(fields=['user_to']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'


User = get_user_model()
User.add_to_class(
    'following',
    models.ManyToManyField(
        'self',
        through=Contact,
        related_name='followers',
        symmetrical=False
    )
)