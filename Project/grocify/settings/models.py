from django.db import models

class ConfigSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.key} → {self.value}"