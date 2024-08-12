# import json

from rest_framework.views import APIView
from rest_framework.response import Response

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
from html_constructor.models import (
    BaseHTMLBlock,
)
from data_connector.serializers import (
    BaseHTMLBlockSerializer,
)


class GetModelsData(APIView):

    def get(self, request):
        # models_names_list = request.GET.get('models_names_list')

        queryset = BaseHTMLBlock.objects.all()
        serializer = BaseHTMLBlockSerializer(queryset, many=True)
        return Response(serializer.data)
    
    
class SetModelsData(APIView):

    def post(self, request):
        data = request.data
        serializer = BaseHTMLBlockSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Data created successfully"}, status=201)
        else:
            return Response(serializer.errors, status=400)


# def set_models_data(request):
#     status = 'error'
#     request_data = request.POST
#     response_data = {}
    
#     return JsonResponse({
#         'status': status,
#         'response_data': response_data,
#     })


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



