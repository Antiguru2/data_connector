from django.urls import include, path
from rest_framework import routers

from . import api
from data_connector.local_api import (
    HHAreaModelViewSet,
    ProjectMetaDataModelViewSet,
)

try:
    from data_connector.local_router import router as local_router
    router = local_router
except ImportError:
    local_router = routers.DefaultRouter()
    local_router.register(r'hh_areas', HHAreaModelViewSet)
    local_router.register(r'project_meta_data', ProjectMetaDataModelViewSet)
    router = local_router


urlpatterns = [
    path('api/', include(router.urls)),

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
    path('api/hh_areas/search/', HHAreaModelViewSet.as_view({'get': 'search'})),
    path('api/hh_areas/get_names_by_ids/', HHAreaModelViewSet.as_view({'get': 'get_names_by_ids'})),
    path('api/all_hh_areas/', HHAreaModelViewSet.as_view({'get': 'list_all'})),
    path('api/project_meta_data/project/<int:project_id>/', ProjectMetaDataModelViewSet.as_view({'get': 'get_by_project'})),
    path('api/project_meta_data/update-for-project/<int:project_id>/', ProjectMetaDataModelViewSet.as_view({'post': 'update_for_project'})),
]