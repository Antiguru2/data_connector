from django.urls import path
# from django.views.generic import TemplateView
# from django.contrib.auth.decorators import login_required

from . import views
from . import api


urlpatterns = [
    path(
        'api/get_models_data/', 
        api.GetModelsData.as_view(),
    ),
    path(
        'api/set_models_data/', 
        api.SetModelsData.as_view(),
    ),
]