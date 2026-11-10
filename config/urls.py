"""
URL Configuration for Student Expense Analytics API.
Routes:
- /dashboard/          -> Hybrid MVT Web Dashboard (Chart.js)
- /api/v1/             -> 30+ RESTful API Endpoints across 5 Modules
- /api/schema/         -> OpenAPI 3 Schema (JSON/YAML)
- /api/schema/swagger/ -> Swagger UI Interactive Documentation
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.finance.views import StudentDashboardTemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Hybrid MVT Dashboard (HTML Template + Chart.js)
    path("dashboard/", StudentDashboardTemplateView.as_view(), name="web-dashboard"),
    # API v1 Endpoints (30+ RESTful APIs)
    path("api/v1/", include("apps.finance.urls")),
    # OpenAPI 3 & Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
