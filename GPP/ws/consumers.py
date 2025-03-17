from channels.generic.websocket import WebsocketConsumer

class FactureConsumer(WebsocketConsumer):

    def connect(self):
        user = self.scope["user"]

        if user.is_authenticated: 
            print('connection accepted')
            self.accept()
        else:
            print('connection rejected')
            self.close()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        pass