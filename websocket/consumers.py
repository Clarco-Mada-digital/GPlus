from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

class NotificationConsumer(WebsocketConsumer):
    
    @staticmethod
    def get_group_name():
        return "notifications"
    
    def connect(self):
        user = self.scope["user"]

        if user.is_authenticated: 
            async_to_sync(self.channel_layer.group_add)(
                self.get_group_name(),
                self.channel_name
            )
            self.accept()
            print('connection accepted')
        else:
            self.close()
            print('connection rejected')

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.get_group_name(), 
            self.channel_name
        )
    
    def signal_clients_changes(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({
            "type": "notification",
            "message": message
        }))