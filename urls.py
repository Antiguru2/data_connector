from django.urls import include, path

from rest_framework import routers

from . import api

try:
    from data_connector.local_router import router as local_router
    router = local_router
except ImportError:
    router = routers.DefaultRouter()


urlpatterns = [
    path('api/', include(router.urls)),

    # api
    path(
        'super-api/<str:natural_key>/',
        api.SuperApiView.as_view(),
    ),
    path(
        'super-api/<str:natural_key>/<int:obj_id>/',
        api.SuperApiView.as_view(),
    ),
    path(
        'super-api/<str:natural_key>/<int:obj_id>/<str:data_type>/',
        api.SuperApiView.as_view(),
    ),
    path(
        'super-api/<str:natural_key>/<int:obj_id>/<str:data_type>/<str:serializer_name>/',
        api.SuperApiView.as_view(),
    ),

]