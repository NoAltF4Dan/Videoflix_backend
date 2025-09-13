from django.apps import AppConfig


class ServiceAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "service_app"
    def ready(self):
        import service_app.signals
