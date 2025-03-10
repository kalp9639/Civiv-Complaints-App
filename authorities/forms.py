from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GovernmentOfficial, ComplaintUpdate, Complaint

class OfficialSignUpForm(UserCreationForm):
    ward_number = forms.CharField(
        max_length=50, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Enter the ward number you are responsible for.'
    )
    department = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Optional: Your department or designation'
    )
    contact_number = forms.CharField(
        max_length=15, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Optional: Your contact number'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        
        if commit:
            user.save()
            # Create GovernmentOfficial profile
            GovernmentOfficial.objects.create(
                user=user,
                ward_number=self.cleaned_data['ward_number'],
                department=self.cleaned_data.get('department'),
                contact_number=self.cleaned_data.get('contact_number')
            )
        return user

class ComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model = ComplaintUpdate
        fields = ['status', 'update_description', 'proof_image']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'update_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'proof_image': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'status': 'Update Complaint Status',
            'update_description': 'Additional Notes (Optional)',
            'proof_image': 'Proof Image (Required)'
        }

    def clean_proof_image(self):
        proof_image = self.cleaned_data.get('proof_image')
        if not proof_image:
            raise forms.ValidationError("Proof image is required when updating complaint status.")
        return proof_image