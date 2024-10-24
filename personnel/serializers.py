from rest_framework import serializers
from .models import Employee, Conge, Notification, Schedule, AgendaEvent, Historique, UserSettings, Paie, \
    UserNotification
from django.contrib.auth import get_user_model,authenticate

user = get_user_model()


class RefusCongeSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)

class EmployeeSerializer(serializers.ModelSerializer):

    poste = serializers.StringRelatedField()
    type_salarie = serializers.StringRelatedField()
    statut = serializers.StringRelatedField()
    departement = serializers.StringRelatedField()
    class Meta:
        model = Employee
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class UserNotificationSerializer(serializers.ModelSerializer):

    notification_user = serializers.CharField(source='notification.user.photo')
    notification_type = serializers.CharField(source='notification.get_type_display')
    notification_message = serializers.CharField(source='notification.message')
    notification_date_created = serializers.DateTimeField(source='notification.date_created')

    class Meta:
        model = UserNotification
        fields = ['notification_user', 'user_affected', 'notification_type', 'notification_message', 'notification_date_created', 'is_read']

class HistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Historique
        fields = '__all__'

class CongeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conge
        fields = '__all__'


class CongesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conge
        fields = ['date_demande', 'date_debut', 'date_fin', 'jours_utilises', 'responsable', 'statut']

    # Ajouter une méthode pour formater les dates
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['date_demande'] = instance.date_demande.strftime('%d/%m/%Y')
        representation['date_debut'] = instance.date_debut.strftime('%d/%m/%Y')
        representation['date_fin'] = instance.date_fin.strftime('%d/%m/%Y')
        return representation

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


class ScheduleListSerializer(serializers.ModelSerializer):
    # Inclure des champs liés à l'employé (image, nom, etc.)
    employee_photo = serializers.ImageField(source='employee.photo')  # Assumant que l'employé a un champ 'photo'
    employee_first_name = serializers.CharField(source='employee.nom')
    employee_last_name = serializers.CharField(source='employee.prenom')
    employee_poste = serializers.CharField(source='employee.poste')
    employee_type = serializers.CharField(source='employee.type_salarie')
    employee_department = serializers.CharField(source='employee.departement')

    # Pour la gestion des horaires
    start_time = serializers.TimeField(format="%H:%M", required=False)
    end_time = serializers.TimeField(format="%H:%M", required=False)
    jour_debut = serializers.CharField()
    jour_fin = serializers.CharField()
    location = serializers.CharField()

    class Meta:
        model = Schedule
        fields = [
            'employee_photo', 'employee_first_name', 'employee_last_name', 'employee_poste',
            'employee_type', 'employee_department', 'start_time', 'end_time', 'jour_debut', 'jour_fin',
            'location'
        ]

    def to_representation(self, instance):
        # Appel à la méthode parent pour obtenir les données de base
        data = super(ScheduleListSerializer, self).to_representation(instance)

        # Regrouper toutes les horaires sur une seule ligne si un employé a plusieurs horaires
        schedules = Schedule.objects.filter(employee=instance.employee)
        grouped_schedule = []

        for schedule in schedules:
            grouped_schedule.append({
                'start_time': schedule.start_time.strftime("%H:%M"),
                'end_time': schedule.end_time.strftime("%H:%M"),
                'jour_debut': schedule.jour_debut,
                'jour_fin': schedule.jour_fin,
                'location': schedule.location
            })

        # Ajouter le regroupement des horaires à la représentation
        data['schedules'] = grouped_schedule

        return data


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['language', 'theme', 'receive_desktop_notifications', 'receive_email_notifications']

class AgendaEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaEvent
        fields = '__all__'


class PaieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paie
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    def validate(self, data):
        email = data.get('email')
        password= data.get('password')
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("Nom d'utilisateur ou mot de passe incorrecte")
        return data