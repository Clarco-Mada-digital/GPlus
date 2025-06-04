from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Serializer personnalisé pour ajouter des informations utilisateur au token JWT
    def validate(self, attrs):
        # Obtenir la réponse standard
        data = super().validate(attrs)
        
        # Ajouter les informations de l'utilisateur directement dans la réponse
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        return data