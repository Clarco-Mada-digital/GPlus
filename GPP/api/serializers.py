from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def validate(self, user):
        token = super().get_token(user)
        token['email'] = user.email # Revendications personnalisées
        return token