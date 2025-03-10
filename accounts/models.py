# accounts/models.py

from django.db import models
from django.contrib.auth.models import User

# We're using the default Django User model for now
# Later, we can extend it with a OneToOneField relationship if needed

# Example of how to extend the User model in the future:
'''
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'
'''