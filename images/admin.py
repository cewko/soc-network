from django.contrib import admin
from django.utils.html import format_html
from .models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "total_likes", "image_preview", "created"]
    list_filter = ["created", "user"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["user"]
    readonly_fields = ["total_likes", "created"]
    list_per_page = 10
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'user', 'url', 'image', 'description')
        }),
        ('Statistics', {
            'fields': ('total_likes', 'created'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
        
    image_preview.short_description = "Preview"