# complaints/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Complaint(models.Model):
    COMPLAINT_TYPES = (
        ('garbage', 'Garbage'),
        ('pothole', 'Pothole'),
        ('cattle', 'Cattle'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    complaint_type = models.CharField(max_length=10, choices=COMPLAINT_TYPES)
    image = models.ImageField(upload_to='complaints/')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='Pending', 
                              choices=(
                                  ('Pending', 'Pending'),
                                  ('In Progress', 'In Progress'),
                                  ('Resolved', 'Resolved'),
                              ))

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    ward_number = models.CharField(max_length=50, null=True, blank=True)     

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_complaint_type_display()} complaint by {self.user.username}"
