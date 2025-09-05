from django.contrib import admin
from django.utils.html import format_html
from .models import Action



@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ["user", "verb", "target_display", "created"]
    list_filter = ["created","verb", "target_ct"]
    search_fields = ["verb", "user__username", "user__email"]
    raw_id_fields = ["user"]
    readonly_fields = ["created"]

    list_per_page = 10

    def target_display(self, obj):
        if obj.target:
            return format_html(
                '<a href="{}">{}</a>',
                obj.target.get_absolute_url() if hasattr(obj.target, 'get_absolute_url') else '#',
                str(obj.target)
            )
        return "No target"

    target_display.short_description = "Target"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'target_ct'
        ).prefetch_related('target')

