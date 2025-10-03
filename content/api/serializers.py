from rest_framework import serializers
from django.conf import settings
from urllib.parse import urljoin

from ..models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for the Video model, including key fields and providing the full URL for the thumbnail."""
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'category', 'thumbnail_url', 'created_at']

    def get_thumbnail_url(self, obj):
        """Returns the absolute URL of the video’s thumbnail if it exists, considering the current request context."""
        if obj.thumbnail_url:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail_url.url)
            return urljoin(settings.MEDIA_URL, obj.thumbnail_url.url)
        return None

    def validate_title(self, value):
        """Ensures the video title contains at least 3 non-whitespace characters."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("The title must contain at least 3 characters.")
        return value
