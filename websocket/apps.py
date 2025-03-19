from django.apps import AppConfig


class WebsocketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'websocket'

    def ready(self):
        # Connecter les signales
        from . import signals
