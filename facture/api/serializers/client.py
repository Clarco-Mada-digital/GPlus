from rest_framework import serializers
from clients.models import Client

class ClientListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = ['id', 'name', 'photo']

class ClientDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = ['id', 'name', 'commercial_name', 'post', 'tel', 'tel2', 'adresse']

