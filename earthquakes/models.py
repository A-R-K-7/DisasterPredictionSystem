from django.db import models

# Create your models here.

class EarthquakeAlert(models.Model):
    magnitude = models.DecimalField(max_digits=4, decimal_places=2)
    location = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Magnitude {self.magnitude} - {self.location}"
