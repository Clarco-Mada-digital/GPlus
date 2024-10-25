from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
  photo = models.ImageField(upload_to='photos/', null=True, blank=True, default="photos/pdp_defaut.png")

  def __str__(self):
    return self.username
