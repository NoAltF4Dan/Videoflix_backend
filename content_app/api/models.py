from django.db import models
from django.contrib.auth.models import User
import uuid


class Profiles(models.Model):
    user = models.OneToOneField(User, verbose_name=("User"), on_delete=models.CASCADE, related_name="abstract_user")
    email_is_confirmed = models.BooleanField(default=False)
    email_token = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return f'Id: {self.user.pk} | {self.user.username}' 
    
    def delete(self, *args, **kwargs):
        self.user.delete()
        super().delete(*args, **kwargs)

class Video(models.Model):
    headline = models.CharField(max_length=50)
    description = models.TextField()
    genre = models.CharField(max_length=65, default="customer",)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.FileField(upload_to="uploads/thumbnails", blank=True)
    url = models.FileField(upload_to="uploads/videos/originals")
    is_converted = models.BooleanField(default=False)
    current_convert_state = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f'Id: {self.pk} | HeadLine: {self.headline} |  Genre:{self.genre} | created at: {self.created_at}' 


class VideoProgress(models.Model):
    profiles = models.ForeignKey(Profiles, on_delete=models.CASCADE, related_name='video_progress')
    updated_at = models.DateTimeField(auto_now=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    current_time = models.FloatField()
    is_finished = models.BooleanField(default=False)


class CurrentVideoConvertProgress(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_convert_progress')
