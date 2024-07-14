from django.apps import AppConfig as DjangoAppConfig # type: ignore


class MyAppConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
