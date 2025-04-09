from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'username')

class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }
                return data
            else:
                raise serializers.ValidationError({
                    'detail': 'Mot de passe incorrect.'
                })
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'detail': 'Aucun utilisateur trouvé avec cet email.'
            })

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass 

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'username', 'current_password', 'new_password')
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        # Vérifier si l'utilisateur essaie de changer le mot de passe
        if attrs.get('new_password'):
            if not attrs.get('current_password'):
                raise serializers.ValidationError({
                    'current_password': 'Le mot de passe actuel est requis pour changer le mot de passe'
                })
            if not self.instance.check_password(attrs.get('current_password')):
                raise serializers.ValidationError({
                    'current_password': 'Mot de passe actuel incorrect'
                })
        return attrs

    def update(self, instance, validated_data):
        # Supprimer les champs de mot de passe des données validées
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)

        # Mettre à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Mettre à jour le mot de passe si fourni
        if new_password:
            instance.set_password(new_password)

        instance.save()
        return instance 