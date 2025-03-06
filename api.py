# # import tempfile
# # import requests

# from rest_framework import (
#     status,
#     permissions,
# )
# # from rest_framework.views import APIView
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.generics import GenericAPIView
# from rest_framework.viewsets import ModelViewSet
# from rest_framework.viewsets import ReadOnlyModelViewSet

# # from django.db import models
# # from django.apps import apps
# # from django.http import Http404, JsonResponse
# # from django.core.files.base import ContentFile
# # from django.core.files.uploadedfile import InMemoryUploadedFile
# # # from django.shortcuts import render, redirect
# # from django.views.decorators.http import require_POST
# # # from django.contrib.sites.shortcuts import get_current_site
# # # from django.views.generic import DetailView
# # # from django.views.decorators.csrf import csrf_exempt
# # # from django.forms import (
# # #     modelform_factory, 
# # # )

# from main.mixins import (
#     ViewSetAndFilterByGetParamsMixin,
# )
# # from html_constructor.models import (
# #     BaseHTMLBlock,
# #     BaseBlocksKit,
# # )
# # from data_connector.serializers import (
# #     DefaultSerializer,
# #     get_serializer_class_by_lower_name,
# # )
# # from data_connector.export_serializers.base_blocks_kit_serializers import (
# #     BaseBlocksKitSerializer,
# # )
# # from html_constructor.models import (
# #     BaseHTMLBlock,
# #     BaseBlocksKit,
# #     Group,
# # )
# # from data_connector.serializers import (
# #     DefaultSerializer,
# #     get_serializer_class_by_lower_name,
# # )
# # from data_connector.export_serializers.base_blocks_kit_serializers import (
# #     BaseBlocksKitSerializer,
# #     BaseHTMLBlockSerializer,
# # )
# # from data_connector.export_serializers.base_store__base_html_blocks_serializers import (
# #     BaseHTMLBlockSerializer,
# #     GroupSerializer,
# # )


# # class BaseHTMLBlockUpdate(APIView):

# #     def get(self, request):
# #         serializer_lower_name = request.GET.get('serializer_lower_name')
# #         SomeSerializerClass = None
# #         if serializer_lower_name:
# #             for serializer_class in DefaultSerializer.__subclasses__():
# #                 if serializer_class.__name__.lower() == serializer_lower_name:
# #                     SomeSerializerClass = serializer_class

# #         if SomeSerializerClass:
# #             SomeClass = SomeSerializerClass.Meta.model
# #             queryset = SomeClass.objects.all()
# #             serializer = SomeSerializerClass(queryset, many=True)

# #         return Response(serializer.data)
    

# #     def post(self, request):
# #         '''
# #             request.data = {
# #                 "group_slug": str,
# #                 "base_html_blocks": [
# #                     {
# #                         "data": {
# #                             "slug": str,
# #                             "name": str,
# #                             "description": str,
# #                             "order": str,
# #                             "template_body": str,
# #                             ...
# #                         },
# #                         "context_items_data": [
# #                             {   
# #                                 "context_item_class_name": str,
# #                                 "data": {
# #                                     "slug": str,
# #                                     "name": str,
# #                                     "description": str,
# #                                     "order": str,
# #                                     ...
# #                                 },
# #                             },
# #                             ...
# #                         ]
# #                     },
# #                     ...
# #                 ],
# #                 ...
# #             }
# #         '''
# #         request_data = request.data

# #         group_slug = request_data.get('group_slug')
# #         base_html_blocks = request_data.get('base_html_blocks')

# #         if group_slug and base_html_blocks:
# #             base_blocks_kit, created = BaseBlocksKit.objects.get_or_create(slug=group_slug)

# #             for base_html_block in base_html_blocks:
# #                 context_items_data = base_html_block.get('context_items_data')
# #                 base_html_block_data = base_html_block.get('data')
# #                 base_html_block['base_blocks_kit'] = base_blocks_kit

# #                 template_body = base_html_block_data.pop('template_body')

# #                 new_base_html_block = BaseHTMLBlock.objects.create(**base_html_block_data)
# #                 new_base_html_block.set_html_to_file(template_body)
                
# #                 for context_item in context_items_data:
# #                     context_item_class_name = context_item.get('context_item_class_name')
# #                     context_item_data = context_item.get('data')
# #                     context_item_class = apps.get_model('html_constructor', context_item_class_name)


# #                     if context_item_class_name == 'textitem':
# #                         pass

# #                     elif context_item_class_name == 'fileitem':
# #                         file_url = context_item_data.pop('file_url')
# #                         response = requests.get(file_url)
# #                         if response.status_code == 200:
# #                             byte_file = response.content
# #                             temp_file = tempfile.NamedTemporaryFile(delete=False)
# #                             temp_file.write(byte_file)
# #                             content_file = ContentFile(byte_file)
# #                             file_name = f"{context_item_class_name.get('slug')}.txt"
# #                             in_memory_file = InMemoryUploadedFile(content_file, None, file_name, "text", content_file.tell(), None)
# #                             new_context_item.file.save(file_name, in_memory_file)
# #                             new_context_item.save()

# #                     elif context_item_class_name == 'querysetitem':
# #                         pass
                        
# #                     elif context_item_class_name == 'htmlblockitem':
# #                         pass

# #                     new_context_item = context_item_class.objects.create(**context_item_data)
# #                     new_context_item.base_html_block = new_base_html_block
# #                     new_context_item.save()

# #             return Response({"message": "Data created successfully"}, status=201)
# #         else:
# #             return Response({}, status=400)


# # from rest_framework import permissions

# # class AllowAnyCreate(permissions.BasePermission):
# #     """
# #     Разрешает создание объектов любому пользователю,
# #     но сохраняет стандартные проверки для других действий.
# #     """

# #     def has_permission(self, request, view):
# #         # Разрешить создание (POST) любому пользователю
# #         if request.method == 'POST':
# #             return True
# #         # Для остальных методов используем стандартные проверки
# #         return permissions.DjangoModelPermissionsOrAnonReadOnly().has_permission(request, view)


# # class GroupsModelViewSet(ModelViewSet):
# #     queryset = Group.objects.all()
# #     serializer_class = GroupSerializer
# #     permission_classes = [AllowAnyCreate]
# #     # permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

# #     def create(self, request, *args, **kwargs):
# #         serializer: GroupSerializer = self.get_serializer(data=request.data, many=True)
# #         serializer.is_valid(raise_exception=True)
# #         self.perform_create(serializer)
# #         headers = self.get_success_headers(serializer.data)
# #         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# # class BaseHTMLBlockModelViewSet(ModelViewSet):
# #     queryset = BaseHTMLBlock.objects.all()
# #     serializer_class = BaseHTMLBlockSerializer
# #     permission_classes = [AllowAnyCreate]
# #     # permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

# #     def create(self, request, *args, **kwargs):
# #         serializer: BaseHTMLBlockSerializer = self.get_serializer(data=request.data, many=True)
# #         serializer.is_valid(raise_exception=True)
# #         self.perform_create(serializer)
# #         headers = self.get_success_headers(serializer.data)
# #         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

# # class BaseBlocksKitModelViewSet(ModelViewSet):
# #     queryset = BaseBlocksKit.objects.all()
# #     # serializer_class = BaseBlocksKitSerializer
# #     # permission_classes = [AllowAnyCreate]
# #     permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

# #     # def get(self, request, *args, **kwargs):
# #     #     return Response({"message": "ok"}, status=status.HTTP_200_OK)

# #     def create(self, request, *args, **kwargs):
# #         serializer: BaseBlocksKitSerializer = self.get_serializer(data=request.data)
# #         serializer.is_valid(raise_exception=True)
# #         self.perform_create(serializer)
# #         headers = self.get_success_headers(serializer.data)
# #         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

# from talent_finder.models import (
#     SearchRow,
#     SearchCriteria,
#     Project, 
#     Candidate, 
#     AnalysisStatistics,
#     Prompt,
# )
# from data_connector.export_serializers.neuro_screener_serializers import (
#     ProjectExportSerializer,
#     SearchCriteriaSerializer, 
#     AnalysisStatisticsExportSerializer,
#     PromptsSerializer,
#     SearchRowSerializer,
# )
# from data_connector.import_serializers.neuro_screener_serializers import CandidateImportSerializer


# class IsStaffPermission(permissions.BasePermission):
#     """
#     Разрешение, которое позволяет доступ только пользователям с is_staff=True.
#     """

#     def has_permission(self, request, view):
#         return request.user and request.user.is_staff
    

# class ProjectsModelViewSet(ModelViewSet):
#     queryset = Project.objects.all()
#     serializer_class = ProjectExportSerializer
#     # permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
#     permission_classes = [permissions.IsAuthenticated, IsStaffPermission]

#     def list(self, request, *args, **kwargs):
#         queryset = Project.objects.none()
#         if request.user:
#             queryset = self.get_queryset().filter(
#                 created_by=request.user
#             )

#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)
    
#     def create(self, request, *args, **kwargs):
#         serializer: ProjectExportSerializer = self.get_serializer(data=request.data)
#         if not request.user.is_authenticated:
#             return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        
#         serializer.initial_data['created_by'] = request.user.id
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
#     # def update(self, request, *args, **kwargs):
#     #     return super().update(request, *args, **kwargs)
    

# from rest_framework.pagination import PageNumberPagination
# from rest_framework.response import Response

# class CustomPageNumberPagination(PageNumberPagination):
#     page_size = 10  # Установить размер страницы по умолчанию
#     page_size_query_param = 'page_size'  # Параметр для указания размера страницы
#     max_page_size = 100  # Максимально допустимый размер страницы

#     def get_paginated_response(self, data):
#         try:
#             next = self.page.next_page_number()
#         except:
#             next = None

#         try:
#             previous = self.page.previous_page_number()
#         except:
#             previous = None

#         # Измените здесь, чтобы настроить, какие данные будут возвращены
#         return Response({
#             'count': self.page.paginator.count,  # Общее количество объектов
#             'next': next,  # URL следующей страницы
#             'previous': previous,  # URL предыдущей страницы
#             'results': data,  # Отфильтрованные результаты
#             # Можете добавить дополнительные поля по своему усмотрению
#             'page_size': self.page_size,
#             'current_page': self.page.number,
#         })


# class CandidateModelViewSet(
#     ViewSetAndFilterByGetParamsMixin,
#     ModelViewSet,
# ):
#     queryset = Candidate.objects.all().order_by('is_viewed')
#     serializer_class = CandidateImportSerializer
#     pagination_class = CustomPageNumberPagination
#     permission_classes = [permissions.IsAuthenticated, IsStaffPermission]


# class AnalysisStatisticsModelViewSet(
#     ViewSetAndFilterByGetParamsMixin,
#     ModelViewSet,
# ):
#     queryset = AnalysisStatistics.objects.all()
#     serializer_class = AnalysisStatisticsExportSerializer
#     pagination_class = CustomPageNumberPagination
#     permission_classes = [permissions.IsAuthenticated, IsStaffPermission]

#     @action(detail=False, methods=['get'], url_path='last')
#     def retrieve_last(self, request):
#         project_id = request.query_params.get('project_id')
#         last_analysis = self.queryset.filter(project_id=project_id).order_by('created_at').last()
#         serializer = self.get_serializer(last_analysis)
#         return Response(serializer.data)
    

# class SearchCriteriaModelViewSet(
#     ViewSetAndFilterByGetParamsMixin,
#     ModelViewSet,
# ):
#     queryset = SearchCriteria.objects.all()
#     serializer_class = SearchCriteriaSerializer
#     pagination_class = CustomPageNumberPagination
#     permission_classes = [permissions.IsAuthenticated, IsStaffPermission]


# class SearchRowModelViewSet(
#     ViewSetAndFilterByGetParamsMixin,
#     ModelViewSet,
# ):
#     queryset = SearchRow.objects.all()
#     serializer_class = SearchRowSerializer
#     pagination_class = CustomPageNumberPagination
#     permission_classes = [permissions.IsAuthenticated, IsStaffPermission]



# class PromptsModelViewSet(
#     ViewSetAndFilterByGetParamsMixin,
#     ModelViewSet,
# ):
#     queryset = Prompt.objects.all()
#     serializer_class = PromptsSerializer
#     pagination_class = CustomPageNumberPagination
#     permission_classes = [permissions.IsAuthenticated, IsStaffPermission]

import json

from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import (
    DataConnector,
)


class SuperApiView(APIView):
    permission_classes = [
        # permissions.AllowAny, 
        permissions.IsAuthenticated, 
    ]

    def get_some_model(self, natural_key, obj_id=None):
        try:
            content_type = ContentType.objects.get_by_natural_key(*natural_key.split('__'))
            some_model = content_type.model_class()
            print('type some_model', type(some_model))
            print('get_some_model some_model', some_model)
            print('get_some_model some_model.__class__.__name__', some_model.__name__)
        except:
            some_model = None


        return some_model
    
    def get_object(self, some_model, obj_id=None):
        if not obj_id:
            return None
        
        return some_model.objects.filter(id=obj_id).first()
    
    def get_queryset(self, some_model, obj_id=None, filter=None):
        if obj_id:
            return some_model.objects.filter(id=obj_id)
        elif filter:
            return some_model.objects.filter(**filter)
        else:
            return some_model.objects.all()
        
    def get_request_data(self, request):
        request_data = {}
        if request.data:
            request_data = request.data
        
        elif request.body:
            request_data = json.loads(request.body)

        return request_data
        
    def get(self, request, natural_key, serializer_name=None, obj_id=None, *args, **kwargs):
        # print('SuperApiView get')
        # print('args', args)
        # print('kwargs', kwargs)

        # print('natural_key', natural_key)
        # print('serializer_name', serializer_name)
        # print('obj_id', obj_id)

        some_model = self.get_some_model(natural_key)
        print('some_model', some_model)
        if not some_model:
            return Response({"status": "error", "message": "Нет модели с таким натуральным ключом"}, status=status.HTTP_404_NOT_FOUND)
        
        
        if obj_id:
            obj = self.get_object(some_model, obj_id)
            print('obj', obj)

            if not obj:
                return Response({"status": "error", "message": "Нет объекта с таким id"}, status=status.HTTP_404_NOT_FOUND)
            
        queryset = self.get_queryset(some_model, obj_id, kwargs)

        if not queryset:
            return Response({"status": "error", "message": "Нет queryset"}, status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = DataConnector.get_serializer(some_model, serializer_name)
        except:
            serializer = None

        print('serializer', serializer)
        if not serializer:
            return Response({"status": "error", "message": "У модели нет сериализатора"}, status=status.HTTP_404_NOT_FOUND)
        
        data = serializer.get_data(queryset)

        if not data:
            return Response({"status": "error", "message": "Нет данных"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"status": "ok", "message": "", "data": data}, status=status.HTTP_200_OK)
    
    # @csrf_exempt
    def post(self, request, natural_key, serializer_name=None, obj_id=None):
        print('post')
        print('request.data', request.data)

        if obj_id:   
            return Response({"message": "Нельзя задать id для создаваемого обьекта"}, status=status.HTTP_404_NOT_FOUND)

        request_data = self.get_request_data(request)

        if not request_data:
            return Response({"message": "Данные не найдены"}, status=status.HTTP_404_NOT_FOUND)

        some_model = self.get_some_model(natural_key)
        if not some_model:
            return Response({"message": "Нет модели с таким натуральным ключом"}, status=status.HTTP_404_NOT_FOUND)

        if type(request_data) == dict:
            input_serializer_data = request_data.get('input_serializer_data')
        else:
            input_serializer_data = None

        try:
            serializer = DataConnector.get_serializer(
                some_model,
                serializer_name, 
                input_serializer_data
            )
        except:
            serializer = None

        if not serializer:
            return Response({"message": "Сериализатор не найден"}, status=status.HTTP_404_NOT_FOUND)       

        comment, response_status, response_data = serializer.set_data(request_data) 

        return Response(
            {
                "message": comment,
                "response_data": response_data,
            }, 
            status=response_status
        )
    
    def put(self, request, natural_key, obj_id=None):
        return Response({"message": "ok"}, status=status.HTTP_200_OK)
    
    def delete(self, request, natural_key, obj_id=None):
        return Response({"message": "ok"}, status=status.HTTP_200_OK)
    
