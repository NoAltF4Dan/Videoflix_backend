from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/", include('service_app.api.urls')),
    path("api/", include('auth_app.api.urls')),
    path('django-rq/', include('django_rq.urls')),
] + debug_toolbar_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
