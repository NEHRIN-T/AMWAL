from django.contrib import admin
from django.urls import path, include
from core.views import dashboard

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]