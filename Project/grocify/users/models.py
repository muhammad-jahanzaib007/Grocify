from django.db import models
from django.contrib.auth.models import User
from inventory.models import Location  # created soon

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    locations = models.ManyToManyField(
        Location,
        blank=True,
        related_name='user_profiles',         # <- reverse accessor for M2M
        help_text="Stores this user can access"
    )
    default_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_profiles'  # <- reverse accessor for FK
    )

