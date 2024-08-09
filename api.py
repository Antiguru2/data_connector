# import json

# from django.apps import apps
from django.http import Http404, JsonResponse
# from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
# from django.contrib.sites.shortcuts import get_current_site
# from django.views.generic import DetailView
# from django.views.decorators.csrf import csrf_exempt
# from django.forms import (
#     modelform_factory, 
# )

# from marketing.models import (
#     Lead
# )
# from site_pages.models import SitePage
# from main.utils import send_message_about_error

@require_POST
def get_models_data(request):
    status = 'error'
    request_data = request.POST
    response_data = {}

    return JsonResponse({
        'status': status,
        'response_data': response_data,
    })

def set_models_data(request):
    status = 'error'
    request_data = request.POST
    response_data = {}
    
    return JsonResponse({
        'status': status,
        'response_data': response_data,
    })


# @csrf_exempt
# @require_POST
# def create_lead(request):
#     """
#     """
#     request_data = request.POST
#     print(request_data)
#     status = 'error'
#     response_data = {}

#     lead_form = modelform_factory(
#         Lead, 
#         fields='__all__',
#     )(request_data)

#     if lead_form.is_valid():
#         lead = lead_form.save()
#         print('lead', lead)
#         status = 'ok'

#     response_data['status'] = status
#     redirect_url = request.META.get('HTTP_REFERER')
#     return redirect(redirect_url)



