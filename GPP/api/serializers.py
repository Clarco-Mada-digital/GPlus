from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Serializer personnalisé pour ajouter des informations utilisateur au token JWT
    def validate(self, attrs):
        # Obtenir la réponse standard
        data = super().validate(attrs)
        
        # Ajouter les informations de l'utilisateur directement dans la réponse
        user = self.user

        # Construction de l'URL de la photo si elle existe
        photo_url = None
        if user.photo:
            try:
                photo_url = user.photo.url
            except:
                photo_url = None

        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'photo': photo_url,
        }
        
        return data