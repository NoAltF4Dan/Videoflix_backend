from django.apps import AppConfig

class AuthAppConfig(AppConfig):
    """
    Configuration class for the 'auth_app' Django application.

    Attributes:
        default_auto_field (str): Specifies the default type of primary key field
            for models in this app. Here it uses BigAutoField for large integer IDs.
        name (str): The full Python path to the application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
