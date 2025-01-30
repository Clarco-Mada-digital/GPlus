from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

# Create your models here.
class Client(models.Model):
  """Model definition for client."""

  # TODO: Define fields here
  # Type du client
  C = 'Client'
  P = 'Prospect'
  F = 'Fourniseur'
  CP = 'Client-Prospect'
  CF = 'Client-Fourniseur'
  TYPE_CHOICES = [
    (C, 'Client'),
    (P, 'Prospect'),
    (F, 'Fourniseur'),
    (CP, 'Client-Prospect'),
    (CF, 'Client-Fourniseur')
  ]
  photo = models.ImageField(upload_to='photos/', blank=True , default="photos/pdp_defaut.png")
  name = models.CharField(max_length=50)
  commercial_name = models.CharField(max_length=50, blank=True)
  post = models.CharField(max_length=50)
  tel = models.CharField(max_length=20, blank=True)
  tel2 = models.CharField(max_length=20, blank=True)
  email = models.EmailField(blank=True)
  adresse = models.CharField(max_length=100, null=True, blank=True)
  type_client = models.CharField(max_length=20, choices=TYPE_CHOICES, null=False, default='Client')
  disponibilite = models.JSONField(blank=True, default=None)
  description_facture = models.TextField(blank=True)
  # history = HistoricalRecords()
  created_at = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(default=timezone.now)

  class Meta:
    """Meta definition for client."""
    verbose_name = 'client'
    verbose_name_plural = 'clients'
    

  def __str__(self):
    """Unicode representation of client."""
    display_name = self.commercial_name or self.name
    return f"{display_name} ({self.get_type_client_display()})"
