# content_app/apps.py
from django.apps import AppConfig

class ContentAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content_app"

    def ready(self):
        import content_app.signals
