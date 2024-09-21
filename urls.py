from django.urls import include, path
# from django.views.generic import TemplateView
# from django.contrib.auth.decorators import login_required

from rest_framework import routers

from . import views
from . import api

router = routers.DefaultRouter()
router.register(r'api/base_blocks_kit_update', api.BaseBlocksKitModelViewSet)


urlpatterns = [
    path('', include(router.urls)),
    # path(
    #     'base_html_block_update/', 
    #     api.BaseHTMLBlockUpdate.as_view(),
    # ),
]