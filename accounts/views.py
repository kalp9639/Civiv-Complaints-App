# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views import View
from django.views.generic import FormView, TemplateView, ListView
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from .forms import SignUpForm


class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'official_profile'):
            context['is_official'] = True
        else:
            context['is_official'] = False
        return context


class SignUpView(FormView):
    template_name = 'signup.html'
    form_class = SignUpForm
    success_url = '/'  # Redirect to home page on success
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated, log them out first
        if request.user.is_authenticated:
            logout(request)
            # Optional: Add a message to inform the user
            messages.info(request, 'You have been logged out to create a new account.')
            # Redirect back to signup page
            return redirect('signup')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)
        messages.success(self.request, f'Account created for {username}! You are now logged in.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request, *args, **kwargs):
        if hasattr(request.user, 'official_profile'):
            # Redirect government officials to their dashboard
            return redirect('authorities:authority_dashboard')
        else:
            # Normal users see their profile with complaint options
            return render(request, 'profile.html', {'user': request.user})


@method_decorator(login_required, name='dispatch')
class NavbarContextView(View):
    def get(self, request, *args, **kwargs):
        context = {}
        if hasattr(request.user, 'official_profile'):
            context['is_official'] = True
        else:
            context['is_official'] = False
        return context


@method_decorator(login_required, name='dispatch')
class HomeRedirectView(View):
    def get(self, request, *args, **kwargs):
        if hasattr(request.user, 'official_profile'):
            return redirect('authorities:authority_dashboard')
        return render(request, 'home.html', {'user': request.user})


class CustomLoginView(LoginView):
    template_name = 'login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated, log them out first
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, 'You have been logged out. Please login with your credentials.')
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')


class UsersListView(ListView):
    model = User
    template_name = 'users.html'
    context_object_name = 'users'