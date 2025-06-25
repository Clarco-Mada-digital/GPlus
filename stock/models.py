from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Categorie(models.Model):
    """Modèle pour les catégories de produits."""
    nom = models.CharField(_('nom'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Fournisseur(models.Model):
    """Modèle pour les fournisseurs de produits."""
    nom = models.CharField(_('nom'), max_length=100)
    email = models.EmailField(_('adresse email'), unique=True)
    telephone = models.CharField(_('téléphone'), max_length=20)
    adresse = models.TextField(_('adresse'))
    contact = models.CharField(_('personne à contacter'), max_length=100, blank=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('fournisseur')
        verbose_name_plural = _('fournisseurs')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.email})"


class Produit(models.Model):
    """Modèle pour les produits en stock."""
    code = models.CharField(_('code'), max_length=50, unique=True)
    designation = models.CharField(_('désignation'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('catégorie')
    )
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('fournisseur principal')
    )
    prix_achat = models.DecimalField(
        _("prix d'achat"),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    prix_vente = models.DecimalField(
        _('prix de vente'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    quantite_stock = models.PositiveIntegerField(_('quantité en stock'), default=0)
    seuil_alerte = models.PositiveIntegerField(_("seuil d'alerte"), default=5)
    photo = models.ImageField(
        _('photo'),
        upload_to='produits/',
        null=True,
        blank=True
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('produit')
        verbose_name_plural = _('produits')
        ordering = ['designation']

    def __str__(self):
        return f"{self.designation} ({self.code})"

    @property
    def statut_stock(self):
        """Retourne le statut du stock (disponible, bientôt épuisé, épuisé)."""
        if self.quantite_stock == 0:
            return 'Épuisé'
        elif self.quantite_stock <= self.seuil_alerte:
            return 'Bientôt épuisé'
        return 'Disponible'


class EntreeStock(models.Model):
    """Modèle pour les entrées en stock."""
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name=_('produit')
    )
    annulee = models.BooleanField(_('annulée'), default=False, help_text=_("Indique si cette entrée a été annulée"))
    quantite = models.PositiveIntegerField(_('quantité'))
    prix_unitaire = models.DecimalField(
        _('prix unitaire'),
        max_digits=10,
        decimal_places=2
    )
    date = models.DateTimeField(_("date d'entrée"), auto_now_add=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('utilisateur')
    )
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('fournisseur')
    )
    reference = models.CharField(_('référence'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _("entrée en stock")
        verbose_name_plural = _("entrées en stock")
        ordering = ['-date']

    def save(self, *args, **kwargs):
        """Met à jour la quantité en stock du produit lors de la sauvegarde."""
        if not self.pk:  # Si c'est une nouvelle entrée
            # Utilisation de F() pour éviter les conditions de course
            from django.db.models import F
            self.produit.quantite_stock = F('quantite_stock') + self.quantite
            self.produit.save(update_fields=['quantite_stock'])
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Met à jour la quantité en stock du produit lors de la suppression."""
        # Utilisation de F() pour éviter les conditions de course
        from django.db.models import F
        self.produit.quantite_stock = F('quantite_stock') - self.quantite
        self.produit.save(update_fields=['quantite_stock'])
        super().delete(*args, **kwargs)

    @property
    def montant_total(self):
        """Calcule le montant total de l'entrée en stock."""
        if self.quantite is None or self.prix_unitaire is None:
            return 0.00
        return float(self.quantite) * float(self.prix_unitaire)


class SortieStock(models.Model):
    """Modèle pour les sorties de stock."""
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name=_('produit')
    )
    quantite = models.PositiveIntegerField(_('quantité'))
    prix_unitaire = models.DecimalField(
        _('prix unitaire'),
        max_digits=10,
        decimal_places=2
    )
    date = models.DateTimeField(_('date de sortie'), auto_now_add=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('utilisateur')
    )
    client = models.CharField(_('client'), max_length=200, blank=True)
    reference = models.CharField(_('référence'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('sortie de stock')
        verbose_name_plural = _('sorties de stock')
        ordering = ['-date']

    def save(self, *args, **kwargs):
        """Vérifie et met à jour la quantité en stock du produit lors de la sauvegarde."""
        if not self.pk:  # Si c'est une nouvelle sortie
            # Vérifier si la quantité en stock est suffisante
            if self.produit.quantite_stock < self.quantite:
                raise ValueError("Quantité en stock insuffisante")
            
            # Utilisation de F() pour éviter les conditions de course
            from django.db.models import F
            self.produit.quantite_stock = F('quantite_stock') - self.quantite
            self.produit.save(update_fields=['quantite_stock'])
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restaure la quantité en stock du produit lors de la suppression."""
        # Utilisation de F() pour éviter les conditions de course
        from django.db.models import F
        self.produit.quantite_stock = F('quantite_stock') + self.quantite
        self.produit.save(update_fields=['quantite_stock'])
        super().delete(*args, **kwargs)

    @property
    def montant_total(self):
        """Calcule le montant total de la sortie du stock."""
        if self.quantite is None or self.prix_unitaire is None:
            return 0.00
        return float(self.quantite) * float(self.prix_unitaire)

    def __str__(self):
        return f"Sortie de {self.quantite} {self.produit.designation} le {self.date.strftime('%d/%m/%Y %H:%M')}"
