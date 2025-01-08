from rest_framework import serializers
from .models import Categorie, OperationEntrer, OperationSortir, Personnel, Fournisseur, Beneficiaire
from django.db.models import Sum, Count

# Sérialiseur pour le modèle Categorie
class CategorieSerializer(serializers.ModelSerializer):
    total_entrees = serializers.SerializerMethodField()
    total_sorties = serializers.SerializerMethodField()
    nombre_entrees = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()

    class Meta:
        model = Categorie
        fields = ['id', 'name', 'description', 'type', 'total_entrees', 'total_sorties', 'nombre_entrees', 'nombre_sorties']

    def get_total_entrees(self, obj):
        return OperationEntrer.objects.filter(categorie=obj).aggregate(total=Sum('montant'))['total'] or 0

    def get_total_sorties(self, obj):
        return OperationSortir.objects.filter(categorie=obj).aggregate(total=Sum('montant'))['total'] or 0

    def get_nombre_entrees(self, obj):
        return OperationEntrer.objects.filter(categorie=obj).count()

    def get_nombre_sorties(self, obj):
        return OperationSortir.objects.filter(categorie=obj).count()

# Sérialiseur pour les détails d'une catégorie (avec les transactions associées)
class CategorieDetailSerializer(serializers.ModelSerializer):
    total_entrees = serializers.SerializerMethodField()
    total_sorties = serializers.SerializerMethodField()
    nombre_entrees = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()
    entrees = serializers.SerializerMethodField()
    sorties = serializers.SerializerMethodField()

    class Meta:
        model = Categorie
        fields = ['id', 'name', 'description', 'type', 'total_entrees', 'total_sorties', 'nombre_entrees', 'nombre_sorties', 'entrees', 'sorties']

    def get_total_entrees(self, obj):
        return OperationEntrer.objects.filter(categorie=obj).aggregate(total=Sum('montant'))['total'] or 0

    def get_total_sorties(self, obj):
        return OperationSortir.objects.filter(categorie=obj).aggregate(total=Sum('montant'))['total'] or 0

    def get_nombre_entrees(self, obj):
        return OperationEntrer.objects.filter(categorie=obj).count()

    def get_nombre_sorties(self, obj):
        return OperationSortir.objects.filter(categorie=obj).count()

    def get_entrees(self, obj):
        entrees = OperationEntrer.objects.filter(categorie=obj)
        return OperationEntrerSerializer(entrees, many=True).data

    def get_sorties(self, obj):
        sorties = OperationSortir.objects.filter(categorie=obj)
        return OperationSortirSerializer(sorties, many=True).data

# Sérialiseur pour le modèle OperationEntrer
class OperationEntrerSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)

    class Meta:
        model = OperationEntrer
        fields = ['id', 'description', 'montant', 'date', 'date_transaction', 'categorie']

# Sérialiseur pour le modèle OperationSortir
class OperationSortirSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)
    beneficiaire = serializers.SerializerMethodField()
    fournisseur = serializers.SerializerMethodField()

    class Meta:
        model = OperationSortir
        fields = ['id', 'description', 'montant', 'date', 'date_de_sortie', 'quantite', 'categorie', 'beneficiaire', 'fournisseur']

    def get_beneficiaire(self, obj):
        if obj.beneficiaire.personnel:
            return {
                "id": obj.beneficiaire.personnel.id,
                "name": f"{obj.beneficiaire.personnel.last_name} {obj.beneficiaire.personnel.first_name}"
            }
        elif obj.beneficiaire.name:
            return {
                "id": obj.beneficiaire.id,
                "name": obj.beneficiaire.name
            }
        return None

    def get_fournisseur(self, obj):
        return {
            "id": obj.fournisseur.id,
            "name": obj.fournisseur.name
        }

# Sérialiseur pour le modèle Personnel
class PersonnelSerializer(serializers.ModelSerializer):
    total_sorties = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()

    class Meta:
        model = Personnel
        fields = ['id', 'last_name', 'first_name', 'tel', 'email', 'date_embauche', 
                 'sexe', 'date_naissance', 'photo', 'adresse', 'type_personnel', 
                 'total_sorties', 'nombre_sorties']

    def get_total_sorties(self, obj):
        # Accéder aux opérations de sortie via le bénéficiaire lié au personnel
        beneficiaires = Beneficiaire.objects.filter(personnel=obj)
        return OperationSortir.objects.filter(beneficiaire__in=beneficiaires).aggregate(
            total=Sum('montant'))['total'] or 0

    def get_nombre_sorties(self, obj):
        beneficiaires = Beneficiaire.objects.filter(personnel=obj)
        return OperationSortir.objects.filter(beneficiaire__in=beneficiaires).count()

class PersonnelDetailSerializer(serializers.ModelSerializer):
    total_sorties = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()
    sorties = serializers.SerializerMethodField()

    class Meta:
        model = Personnel
        fields = ['id', 'last_name', 'first_name', 'tel', 'email', 'date_embauche',
                 'sexe', 'date_naissance', 'photo', 'adresse', 'type_personnel',
                 'total_sorties', 'nombre_sorties', 'sorties']

    def get_total_sorties(self, obj):
        beneficiaires = Beneficiaire.objects.filter(personnel=obj)
        return OperationSortir.objects.filter(beneficiaire__in=beneficiaires).aggregate(
            total=Sum('montant'))['total'] or 0

    def get_nombre_sorties(self, obj):
        beneficiaires = Beneficiaire.objects.filter(personnel=obj)
        return OperationSortir.objects.filter(beneficiaire__in=beneficiaires).count()

    def get_sorties(self, obj):
        beneficiaires = Beneficiaire.objects.filter(personnel=obj)
        sorties = OperationSortir.objects.filter(beneficiaire__in=beneficiaires)
        return OperationSortirSerializer(sorties, many=True).data

# Sérialiseur pour le modèle Fournisseur
class FournisseurSerializer(serializers.ModelSerializer):
    total_sorties = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()

    class Meta:
        model = Fournisseur
        fields = ['id', 'name', 'contact', 'total_sorties', 'nombre_sorties']

    def get_total_sorties(self, obj):
        return OperationSortir.objects.filter(fournisseur=obj).aggregate(total=Sum('montant'))['total'] or 0

    def get_nombre_sorties(self, obj):
        return OperationSortir.objects.filter(fournisseur=obj).count()

class FournisseurDetailSerializer(serializers.ModelSerializer):
    total_sorties = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()
    sorties = serializers.SerializerMethodField()

    class Meta:
        model = Fournisseur
        fields = ['id', 'name', 'contact', 'total_sorties', 'nombre_sorties', 'sorties']

    def get_total_sorties(self, obj):
        return OperationSortir.objects.filter(fournisseur=obj).aggregate(
            total=Sum('montant'))['total'] or 0

    def get_nombre_sorties(self, obj):
        return OperationSortir.objects.filter(fournisseur=obj).count()

    def get_sorties(self, obj):
        sorties = OperationSortir.objects.filter(fournisseur=obj)
        return OperationSortirSerializer(sorties, many=True).data

# Sérialiseur pour le modèle Beneficiaire
class BeneficiaireSerializer(serializers.ModelSerializer):
    total_sorties = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiaire
        fields = ['id', 'name', 'total_sorties', 'nombre_sorties']

    def get_total_sorties(self, obj):
        return OperationSortir.objects.filter(beneficiaire=obj).aggregate(total=Sum('montant'))['total'] or 0

    def get_nombre_sorties(self, obj):
        return OperationSortir.objects.filter(beneficiaire=obj).count()

class BeneficiaireDetailSerializer(serializers.ModelSerializer):
    total_sorties = serializers.SerializerMethodField()
    nombre_sorties = serializers.SerializerMethodField()
    sorties = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiaire
        fields = ['id', 'name', 'total_sorties', 'nombre_sorties', 'sorties']

    def get_total_sorties(self, obj):
        return OperationSortir.objects.filter(beneficiaire=obj).aggregate(
            total=Sum('montant'))['total'] or 0

    def get_nombre_sorties(self, obj):
        return OperationSortir.objects.filter(beneficiaire=obj).count()

    def get_sorties(self, obj):
        sorties = OperationSortir.objects.filter(beneficiaire=obj)
        return OperationSortirSerializer(sorties, many=True).data

# Modifier le sérialiseur OperationSortirSerializer
class OperationSortirCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationSortir
        fields = ['description', 'montant', 'date_de_sortie', 'quantite', 'categorie', 'beneficiaire', 'fournisseur']
        extra_kwargs = {
            'categorie': {'write_only': True},
            'beneficiaire': {'write_only': True},
            'fournisseur': {'write_only': True}
        }

    def validate(self, data):
        # Vérifier que la catégorie est de type 'sortie'
        if data['categorie'].type != 'sortie':
            raise serializers.ValidationError(
                {"categorie": "La catégorie doit être de type 'sortie'"}
            )
        return data

    def to_representation(self, instance):
        # Après création, retourner la représentation complète avec OperationSortirSerializer
        return OperationSortirSerializer(instance).data

class OperationEntrerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEntrer
        fields = ['description', 'montant', 'date_transaction', 'categorie']
        extra_kwargs = {
            'categorie': {'write_only': True}
        }

    def validate(self, data):
        # Vérifier que la catégorie est de type 'entree'
        if data['categorie'].type != 'entree':
            raise serializers.ValidationError(
                {"categorie": "La catégorie doit être de type 'entree'"}
            )
        return data

    def to_representation(self, instance):
        # Après création, retourner la représentation complète avec OperationEntrerSerializer
        return OperationEntrerSerializer(instance).data