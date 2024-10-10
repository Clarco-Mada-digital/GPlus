from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Employee, UserSettings
from accounts.models import CustomUser

@receiver(post_save, sender=Employee)
def create_user_for_employe(sender, instance, created, **kwargs):
    if created:
        # Création d'un utilisateur avec un mot de passe aléatoire sécurisé
        user = CustomUser.objects.create_user(
            photo=instance.photo,
            username=instance.email.split('@')[0],  # Utiliser la partie avant '@' de l'email comme nom d'utilisateur
            email=instance.email,
            password='123456789',
        )

        # Associer l'utilisateur avec l'employé sans sauvegarder immédiatement (évite le double save)
        instance.user = user

        # Dictionnaire pour mapper les types de salariés aux groupes
        groups_mapping = {
            'salarie': 'Salarié',
            'direction': 'Direction',
            'assit_direction': 'Assistant Direction',  # Correction ici
            'benevole': 'Bénévole',
            'stagiaire': 'Stagiaire',
            'freelance': 'Freelance'
        }

        # Vérifier si l'employé a un type de salarié et ajouter au groupe correspondant
        if instance.type_salarie in groups_mapping:
            group_name = groups_mapping[instance.type_salarie]
            try:
                group = Group.objects.get(name=group_name)
                print(f"Group '{group_name}' found for employee.")

                instance.groupe = group  # Ajouter l'utilisateur au groupe
                print(f"User {user.username} added to group {group_name}.")

                # Ajouter les permissions du groupe à l'employé
                permissions = group.permissions.all()
                # Assigner les permissions à l'employé
                print(permissions)
                if permissions.exists():
                    instance.user.user_permissions.add(*permissions)  # Ajouter les permissions de manière sécurisée
                    print(f"Permissions added to employee {instance.email}.")
                else:
                    print(f"No permissions found for group {group.name}.")

            except Group.DoesNotExist:
                print(f"Group '{group_name}' does not exist.")

        else:
            print(f"Employee type '{instance.type_salarie}' not found in groups_mapping.")

        # Créer les paramètres utilisateur associés
        UserSettings.objects.create(user=user)
        print(f"User settings created for {user.username}.")

        # Sauvegarder la relation entre l'employé et l'utilisateur
        instance.save()
        print(f"Employee {instance.email} saved with linked user.")