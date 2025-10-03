from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Custom Django admin configuration for the Video model,

    displaying key fields, filtering by category and processing status,

    and marking generated video files and processing status as read-only.
    """

    list_display = ['title', 'category', 'processing_status', 'created_at']
    list_filter = ['category', 'processing_status', 'created_at']
    search_fields = ['title', 'description', 'category']
    readonly_fields = ['processing_status', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path', 'thumbnail_url']

    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'description', 'category', 'original_video')
        }),
        ('Processing Status', {
            'fields': ('processing_status',),
            'classes': ('collapse',)
        }),
        ('Generated Files', {
            'fields': ('thumbnail_url', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path'),
            'classes': ('collapse',)
        }),
    )
