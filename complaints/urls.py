# complaints/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.ComplaintCreateView.as_view(), name='submit_complaint'),
    path('list/', views.ComplaintListView.as_view(), name='view_complaints'),
    path('detail/<int:pk>/', views.ComplaintDetailView.as_view(), name='complaint_detail'),
    path('map/', views.MapView.as_view(), name='map_view'),
]

