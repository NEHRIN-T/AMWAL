from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/portfolio-overview/', views.portfolio_overview, name='portfolio-overview'),
    path('dashboard/rental-intelligence/', views.rental_intelligence, name='rental-intelligence'),
    path('dashboard/occupancy/', views.occupancy_view, name='occupancy-view'),
    path('dashboard/financial/', views.financial_view, name='financial-view'),
    path('dashboard/export/', views.export_data, name='export-data'),
    path('property/<int:pk>/', views.property_detail, name='property-detail'),
]
