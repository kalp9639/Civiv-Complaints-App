# complaints/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import Complaint
from .forms import ComplaintForm
import geopandas as gpd
from shapely.geometry import Point
import os
import zipfile
import tempfile
import fiona
import json


def extract_kml_from_kmz(kmz_file):
    # Create a temporary directory to extract files
    temp_dir = tempfile.mkdtemp()
    
    # Extract the KMZ file (which is essentially a ZIP file)
    with zipfile.ZipFile(kmz_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find the KML file in the extracted contents
    for file in os.listdir(temp_dir):
        if file.endswith('.kml'):
            return os.path.join(temp_dir, file)
    
    # If no KML file was found
    raise FileNotFoundError(f"No KML file found in the KMZ archive: {kmz_file}")


def load_kml_as_gdf(kml_file):
    # Use fiona driver to read KML
    with fiona.Env():
        # Sometimes KML files need specific driver settings
        gdf = gpd.read_file(kml_file, driver='KML')
    
    return gdf


kmz_file = "/Users/kalp/Documents/SNU/8th semester/Internship/python101/Django_Civic Complaints/complaints_system/util/Ward_Boundary.kmz"
kml_file = extract_kml_from_kmz(kmz_file)
gdf = load_kml_as_gdf(kml_file)


def find_ward(lat, lon):
    """Finds the ward name for a given latitude and longitude"""
    point = Point(lon, lat)
    for _, row in gdf.iterrows():
        if row.geometry.contains(point):
            return row["Name"]
    return "Unknown"


@method_decorator(login_required, name='dispatch')
class ComplaintCreateView(CreateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = 'complaints/submit_complaint.html'
    success_url = reverse_lazy('view_complaints')
    
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'official_profile'):
            messages.error(request, "Government officials cannot submit complaints.")
            return redirect('authorities:authority_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        complaint = form.save(commit=False)
        complaint.user = self.request.user
        # Assign ward based on lat-long
        if complaint.latitude and complaint.longitude:
            complaint.ward_number = find_ward(complaint.latitude, complaint.longitude)
        complaint.save()
        messages.success(self.request, 'Your complaint has been submitted successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ComplaintListView(ListView):
    model = Complaint
    template_name = 'complaints/view_complaints.html'
    context_object_name = 'complaints'
    
    def get_queryset(self):
        return Complaint.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class ComplaintDetailView(DetailView):
    model = Complaint
    template_name = 'complaints/complaint_detail.html'
    context_object_name = 'complaint'
    
    def dispatch(self, request, *args, **kwargs):
        # Get the complaint object
        complaint = self.get_object()
        
        # Check if user is official for this ward
        is_official = False
        if hasattr(request.user, 'official_profile'):
            is_official = (request.user.official_profile.ward_number == complaint.ward_number)
            
        # Allow access if the user is the submitter or a government official in the same ward
        if request.user == complaint.user or is_official:
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(request, "You do not have permission to view this complaint.")
            return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaint = self.get_object()
        
        # Check if user is official for this ward
        is_official = False
        if hasattr(self.request.user, 'official_profile'):
            is_official = (self.request.user.official_profile.ward_number == complaint.ward_number)
        
        # Fetch all updates in descending order (latest first)
        updates = complaint.updates.order_by('-updated_at')
        
        context['is_official'] = is_official
        context['updates'] = updates
        return context


@method_decorator(login_required, name='dispatch')
class MapView(View):
    template_name = 'complaints/map_view.html'
    
    def get(self, request, *args, **kwargs):
        # Get all complaints with coordinates
        complaints = Complaint.objects.filter(
            user=request.user, 
            latitude__isnull=False, 
            longitude__isnull=False
        )
        
        # Prepare complaints data for the map
        complaints_data = []
        for complaint in complaints:
            complaints_data.append({
                'id': complaint.id,
                'lat': float(complaint.latitude),
                'lng': float(complaint.longitude),
                'type': complaint.get_complaint_type_display(),
                'status': complaint.status,
                'url': f'/complaints/detail/{complaint.id}/',  # URL to complaint details
                'ward': complaint.ward_number or 'Unknown',
                'submitted_by': complaint.user.get_full_name() or complaint.user.username,
                'date': complaint.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Pass the complaints data to the template
        context = {
            'complaints_data': json.dumps(complaints_data),
            'complaint_count': len(complaints_data),
        }
        
        return render(request, self.template_name, context)