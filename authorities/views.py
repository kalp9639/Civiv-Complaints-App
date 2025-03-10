# authorities/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views import View
from django.views.generic import FormView, TemplateView, ListView, DetailView, UpdateView
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from .forms import OfficialSignUpForm, ComplaintUpdateForm
from complaints.models import Complaint
from .models import GovernmentOfficial, ComplaintUpdate
import json


@method_decorator(csrf_protect, name='dispatch')
class OfficialSignUpView(FormView):
    template_name = 'authorities/official_signup.html'
    form_class = OfficialSignUpForm
    success_url = '/authorities/dashboard/'  # Adjust as needed
    
    def form_valid(self, form):
        try:
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(self.request, user)
            messages.success(self.request, f'Official account created for {username}!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error creating account: {str(e)}')
            return self.form_invalid(form)


class OfficialLoginView(View):
    template_name = 'authorities/official_login.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                official = user.official_profile
                login(request, user)
                messages.success(request, f'Welcome, {user.get_full_name()}!')
                return redirect('authorities:authority_dashboard')
            except GovernmentOfficial.DoesNotExist:
                messages.error(request, 'You are not registered as a government official.')
        else:
            messages.error(request, 'Invalid username or password.')
        
        return render(request, self.template_name)


class OfficialLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('authorities:official_login')


@method_decorator(login_required, name='dispatch')
class AuthorityDashboardView(TemplateView):
    template_name = 'authorities/authority_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            self.official = request.user.official_profile
            return super().dispatch(request, *args, **kwargs)
        except GovernmentOfficial.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a government official.')
            return redirect('authorities:official_login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaints = Complaint.objects.filter(ward_number=self.official.ward_number)
        
        context.update({
            'official': self.official,
            'total_complaints': complaints.count(),
            'pending_complaints': complaints.filter(status='Pending').count(),
            'in_progress_complaints': complaints.filter(status='In Progress').count(),
            'resolved_complaints': complaints.filter(status='Resolved').count(),
        })
        return context


@method_decorator(login_required, name='dispatch')
class AuthorityComplaintsListView(ListView):
    template_name = 'authorities/authority_complaints_list.html'
    context_object_name = 'complaints'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            self.official = request.user.official_profile
            return super().dispatch(request, *args, **kwargs)
        except GovernmentOfficial.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a government official.')
            return redirect('home')
    
    def get_queryset(self):
        return Complaint.objects.filter(ward_number=self.official.ward_number)


@method_decorator(login_required, name='dispatch')
class AuthorityComplaintsMapView(View):
    template_name = 'authorities/authority_complaints_map.html'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            self.official = request.user.official_profile
            return super().dispatch(request, *args, **kwargs)
        except GovernmentOfficial.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a government official.')
            return redirect('home')
    
    def get(self, request, *args, **kwargs):
        complaints = Complaint.objects.filter(ward_number=self.official.ward_number)
        
        # Prepare complaints data for map
        complaints_data = []
        for complaint in complaints:
            complaints_data.append({
                'id': complaint.id,
                'lat': float(complaint.latitude),
                'lng': float(complaint.longitude),
                'type': complaint.get_complaint_type_display(),
                'status': complaint.status,
                'url': f'/complaints/detail/{complaint.id}/',
                'ward': complaint.ward_number or 'Unknown',
                'submitted_by': complaint.user.get_full_name() or complaint.user.username,
                'date': complaint.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        context = {
            'complaints_data': json.dumps(complaints_data),
            'complaint_count': len(complaints_data),
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class UpdateComplaintStatusView(View):
    template_name = 'authorities/update_complaint_status.html'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            self.official = request.user.official_profile
            self.complaint = get_object_or_404(
                Complaint, 
                id=kwargs.get('complaint_id'), 
                ward_number=self.official.ward_number
            )
            return super().dispatch(request, *args, **kwargs)
        except GovernmentOfficial.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a government official.')
            return redirect('home')
    
    def get(self, request, *args, **kwargs):
        form = ComplaintUpdateForm(initial={'status': self.complaint.status})
        return render(request, self.template_name, {
            'form': form, 
            'complaint': self.complaint
        })
    
    def post(self, request, *args, **kwargs):
        form = ComplaintUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.complaint = self.complaint
            update.official = self.official
            update.save()
            
            self.complaint.status = form.cleaned_data['status']
            self.complaint.save()
            
            messages.success(request, 'Complaint status updated successfully!')
            return redirect('authorities:authority_complaints_list')
        
        return render(request, self.template_name, {
            'form': form, 
            'complaint': self.complaint
        })


@method_decorator(login_required, name='dispatch')
class OfficialComplaintsView(ListView):
    template_name = 'authority_complaints_list.html'
    context_object_name = 'complaints'
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'official_profile'):
            messages.error(request, "You do not have permission to access this page.")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Complaint.objects.filter(ward_number=self.request.user.official_profile.ward_number)


@method_decorator(login_required, name='dispatch')
class BaseTemplateUpdateView(TemplateView):
    template_name = 'base.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_official'] = hasattr(self.request.user, 'official_profile')
        return context


@method_decorator(login_required, name='dispatch')
class ComplaintDetailView(DetailView):
    model = Complaint
    template_name = 'complaints/complaint_detail.html'
    context_object_name = 'complaint'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            self.official = request.user.official_profile
            self.complaint = self.get_object()
            
            # Check if this official is authorized to view this complaint
            if self.complaint.ward_number != self.official.ward_number:
                messages.error(request, 'You do not have permission to view this complaint.')
                return redirect('home')
                
            return super().dispatch(request, *args, **kwargs)
        except GovernmentOfficial.DoesNotExist:
            messages.error(request, 'Access denied. You are not registered as a government official.')
            return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add is_official flag and ordered updates
        context.update({
            'is_official': True,
            'updates': self.complaint.updates.order_by('-updated_at')
        })
        
        return context