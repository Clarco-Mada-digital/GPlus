from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from facture.models import Entreprise
from facture.api.serializers import EntrepriseSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    # Serializer personnalisé pour ajouter des informations utilisateur au token JWT
    def validate(self, attrs):
        # Obtenir la réponse standard
        data = super().validate(attrs)
        
        # Ajouter les informations de l'utilisateur directement dans la réponse
        user = self.user
        photo_url = self.getUserPhotoUrl()
        entreprise = self.getUserEntepriseData()

        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'photo': photo_url,
            'entreprise': entreprise
        }
        
        return data
    
    def getUserEntepriseData(self):
        entreprise = Entreprise.objects.first()

        if entreprise:
            return EntrepriseSerializer(entreprise).data

        return None


    def getUserPhotoUrl(self):
        photo_url = None

        if self.user.photo:
            try:
                photo_url = self.user.photo.url
            except:
                photo_url = None
        
        return photo_url