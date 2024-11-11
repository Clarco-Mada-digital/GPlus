from django.contrib.auth import get_user_model  # Utilise le modèle d'utilisateur personnalisé
from .models import Notification, UserNotification  # Importez vos modèles

# Création d'une notification pour une action spécifique
def create_notification(user_action, user_affected, message,type):
    # Crée la notification
    notification = Notification.objects.create(
        user=user_action,  # L'utilisateur qui effectue l'action
        message=message,
        type=type
    )

    # Associe cette notification à l'utilisateur affecté
    user_notification = UserNotification.objects.create(
        user_affected=user_affected,  # L'utilisateur affectéd
        notification=notification
    )

    return user_notification

def create_global_notification(user_action,type, message):
    # Crée la notification globale
    notification = Notification.objects.create(
        user=user_action,
        message=message,
        type=type,
        is_global=True
    )

    # Récupère tous les utilisateurs en utilisant le modèle personnalisé
    CustomUser = get_user_model()
    all_users = CustomUser.objects.all()

    # Crée une notification pour chaque utilisateur
    for user in all_users:
        UserNotification.objects.create(
            user_affected=user,
            notification=notification
        )

    return notification


