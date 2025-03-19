from django.db.models.signals import post_save
from django.dispatch import receiver
from facture.models import Facture
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .consumers import NotificationConsumer
 
@receiver(post_save, sender=Facture, dispatch_uid="send_facture_table_updated_to_clients")
def send_facture_table_updated_to_clients(sender, created, **kwargs):
    """Notifie les action save du modèle facture"""
    if created: 
        return
    
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        NotificationConsumer.get_group_name(),
        {
            "type": "signal_clients_changes",
            "message": "Facture table updated"
        }
    )
    
    print('facture table updated')
