from django.urls import path
# from django.views.generic import TemplateView
# from django.contrib.auth.decorators import login_required

from . import views
from . import api


urlpatterns = [
    path(
        'base_html_block_update/', 
        api.BaseHTMLBlockUpdate.as_view(),
    ),
    path(
        'base_blocks_kit_update/', 
        api.BaseBlocksKitUpdate.as_view(),
    ),
]