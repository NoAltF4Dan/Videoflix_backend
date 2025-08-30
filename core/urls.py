"""
Core URL configuration for the Videoflix backend.

Routes:
- /admin/ → Django Admin
- /api/ → Auth endpoints (Register, Login, etc.)
- /api/video/ → Video streaming endpoints
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),       # Auth endpoints
    path('api/video/', include('content_app.api.urls'))  # Video endpoints
]
