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
  commercial_name = models.CharField(max_length=50, default=None)
  post = models.CharField(max_length=50)
  tel = models.CharField(max_length=15, default=None)
  tel2 = models.CharField(max_length=15, default=None)
  email = models.EmailField()
  adresse = models.CharField(max_length=100, null=True)
  type_client = models.CharField(max_length=20, choices=TYPE_CHOICES, null=False, default='Client')
  history = HistoricalRecords()
  created_at = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(default=timezone.now)

  class Meta:
    """Meta definition for client."""

    verbose_name = 'client'
    verbose_name_plural = 'clients'

  def __str__(self):
    """Unicode representation of client."""
    return f"{self.name} ({self.get_type_display()})"
