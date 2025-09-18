"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from pathlib import Path

urlpatterns = [
    # API endpoints should be first so they take precedence.
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]

schema_view = get_schema_view(
   openapi.Info(
      title="Simple Commerce API",
      default_version='v1',
      description="REST API for products, carts, orders, auth, and addresses.",
      contact=openapi.Contact(email="support@example.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def get_full_url(request):
    scheme = request.scheme
    host = request.get_host()
    forwarded_port = request.META.get("HTTP_X_FORWARDED_PORT")

    if ':' not in host and forwarded_port:
        host = f"{host}:{forwarded_port}"

    return f"{scheme}://{host}"

@csrf_exempt
def dynamic_schema_view(request, *args, **kwargs):
    url = get_full_url(request)
    view = get_schema_view(
        openapi.Info(
            title="Simple Commerce API",
            default_version='v1',
            description="REST API for products, carts, orders, auth, and addresses.",
            contact=openapi.Contact(email="support@example.com"),
        ),
        public=True,
        url=url,
    )
    return view.with_ui('swagger', cache_timeout=0)(request)

urlpatterns += [
    re_path(r'^docs/$', dynamic_schema_view, name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^swagger\.json$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

def spa_index_view(request, path=None):
    """
    PUBLIC_INTERFACE
    Serve the React SPA index.html for any non-API, non-admin route.
    This enables client-side routing for the React app in production deployments
    where Django serves the frontend build.
    """
    # Expected build path: BASE_DIR / 'frontend_build' / 'index.html'
    index_path: Path = Path(settings.BASE_DIR) / 'frontend_build' / 'index.html'
    if index_path.exists():
        try:
            with open(index_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='text/html')
        except Exception:
            return HttpResponseNotFound("Frontend build not found or unreadable.")
    return HttpResponseNotFound("Frontend build not found. Ensure React is built and copied to 'frontend_build'.")

# Catch-all: anything not starting with /api or /admin or known docs should go to SPA
# Put this at the very end to not override API/docs/admin paths.
urlpatterns += [
    re_path(r'^(?!api/|admin/|docs/|redoc/|swagger\.json).*$', spa_index_view, name='spa-fallback'),
]