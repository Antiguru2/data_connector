from django.urls import include, path

from rest_framework import routers

try:
    from data_connector.local_router import router as local_router
    router = local_router
except ImportError:
    router = routers.DefaultRouter()


urlpatterns = [
    path('api/', include(router.urls)),
]