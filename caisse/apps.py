from django.apps import AppConfig


class CaisseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caisse'

class CaisseConfig(AppConfig):
    name = 'caisse'

    def ready(self):
        import caisse.signals