from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('users/', views.UsersListView.as_view(), name='users'),
    path('home/', views.HomeRedirectView.as_view(), name='home_view'),
]