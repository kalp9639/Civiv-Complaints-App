# complaints/forms.py

from django import forms
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['complaint_type', 'image', 'description', 'latitude', 'longitude']
        widgets = {
            'complaint_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide additional details about the issue (optional)'}),
        }
        labels = {
            'complaint_type': 'Type of Issue',
            'image': 'Upload Image of the Issue',
            'description': 'Description (Optional)',
        }
        help_texts = {
            'image': 'Please provide a clear image of the issue.',
        }