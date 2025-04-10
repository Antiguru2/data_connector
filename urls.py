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

    # form
    path(
        'super-api/form/<str:natural_key>/',
        api.SuperApiFormView.as_view(),
    ),
    path(
        'super-api/form/<str:natural_key>/<int:obj_id>/',
        api.SuperApiFormView.as_view(),
    ),
    path(
        'super-api/form/<str:natural_key>/<str:serializer_name>/',
        api.SuperApiFormView.as_view(),
    ),
    path(
        'super-api/form/<str:natural_key>/<str:serializer_name>/<int:obj_id>/',
        api.SuperApiFormView.as_view(),
    ),

    # data
    path(
        'super-api/<str:natural_key>/',
        api.SuperApiView.as_view(),
    ),
    path(
        'super-api/<str:natural_key>/<int:obj_id>/',
        api.SuperApiView.as_view(),
    ),
    path(
        'super-api/<str:natural_key>/<str:serializer_name>/',
        api.SuperApiView.as_view(),
    ),
    path(
        'super-api/<str:natural_key>/<str:serializer_name>/<int:obj_id>/',
        api.SuperApiView.as_view(),
    ),

]