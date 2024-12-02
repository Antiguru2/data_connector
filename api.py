import tempfile
import requests

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django.db import models
from django.apps import apps
from django.http import Http404, JsonResponse
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
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
    BaseBlocksKit,
    Group,
)
from data_connector.serializers import (
    DefaultSerializer,
    get_serializer_class_by_lower_name,
)
# from data_connector.export_serializers.base_blocks_kit_serializers import (
#     BaseBlocksKitSerializer,
#     BaseHTMLBlockSerializer,
# )
from data_connector.export_serializers.base_store__base_html_blocks_serializers import (
    BaseHTMLBlockSerializer,
    GroupSerializer,
)


class BaseHTMLBlockUpdate(APIView):

    def get(self, request):
        serializer_lower_name = request.GET.get('serializer_lower_name')
        SomeSerializerClass = None
        if serializer_lower_name:
            for serializer_class in DefaultSerializer.__subclasses__():
                if serializer_class.__name__.lower() == serializer_lower_name:
                    SomeSerializerClass = serializer_class

        if SomeSerializerClass:
            SomeClass = SomeSerializerClass.Meta.model
            queryset = SomeClass.objects.all()
            serializer = SomeSerializerClass(queryset, many=True)

        return Response(serializer.data)
    

    def post(self, request):
        '''
            request.data = {
                "group_slug": str,
                "base_html_blocks": [
                    {
                        "data": {
                            "slug": str,
                            "name": str,
                            "description": str,
                            "order": str,
                            "template_body": str,
                            ...
                        },
                        "context_items_data": [
                            {   
                                "context_item_class_name": str,
                                "data": {
                                    "slug": str,
                                    "name": str,
                                    "description": str,
                                    "order": str,
                                    ...
                                },
                            },
                            ...
                        ]
                    },
                    ...
                ],
                ...
            }
        '''
        request_data = request.data

        group_slug = request_data.get('group_slug')
        base_html_blocks = request_data.get('base_html_blocks')

        if group_slug and base_html_blocks:
            base_blocks_kit, created = BaseBlocksKit.objects.get_or_create(slug=group_slug)

            for base_html_block in base_html_blocks:
                context_items_data = base_html_block.get('context_items_data')
                base_html_block_data = base_html_block.get('data')
                base_html_block['base_blocks_kit'] = base_blocks_kit

                template_body = base_html_block_data.pop('template_body')

                new_base_html_block = BaseHTMLBlock.objects.create(**base_html_block_data)
                new_base_html_block.set_html_to_file(template_body)
                
                for context_item in context_items_data:
                    context_item_class_name = context_item.get('context_item_class_name')
                    context_item_data = context_item.get('data')
                    context_item_class = apps.get_model('html_constructor', context_item_class_name)


                    if context_item_class_name == 'textitem':
                        pass

                    elif context_item_class_name == 'fileitem':
                        file_url = context_item_data.pop('file_url')
                        response = requests.get(file_url)
                        if response.status_code == 200:
                            byte_file = response.content
                            temp_file = tempfile.NamedTemporaryFile(delete=False)
                            temp_file.write(byte_file)
                            content_file = ContentFile(byte_file)
                            file_name = f"{context_item_class_name.get('slug')}.txt"
                            in_memory_file = InMemoryUploadedFile(content_file, None, file_name, "text", content_file.tell(), None)
                            new_context_item.file.save(file_name, in_memory_file)
                            new_context_item.save()

                    elif context_item_class_name == 'querysetitem':
                        pass
                        
                    elif context_item_class_name == 'htmlblockitem':
                        pass

                    new_context_item = context_item_class.objects.create(**context_item_data)
                    new_context_item.base_html_block = new_base_html_block
                    new_context_item.save()

            return Response({"message": "Data created successfully"}, status=201)
        else:
            return Response({}, status=400)


from rest_framework import permissions

class AllowAnyCreate(permissions.BasePermission):
    """
    Разрешает создание объектов любому пользователю,
    но сохраняет стандартные проверки для других действий.
    """

    def has_permission(self, request, view):
        # Разрешить создание (POST) любому пользователю
        if request.method == 'POST':
            return True
        # Для остальных методов используем стандартные проверки
        return permissions.DjangoModelPermissionsOrAnonReadOnly().has_permission(request, view)


class GroupsModelViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [AllowAnyCreate]
    # permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

    def create(self, request, *args, **kwargs):
        serializer: GroupSerializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BaseHTMLBlockModelViewSet(ModelViewSet):
    queryset = BaseHTMLBlock.objects.all()
    serializer_class = BaseHTMLBlockSerializer
    permission_classes = [AllowAnyCreate]
    # permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

    def create(self, request, *args, **kwargs):
        serializer: BaseHTMLBlockSerializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

class BaseBlocksKitModelViewSet(ModelViewSet):
    queryset = BaseBlocksKit.objects.all()
    # serializer_class = BaseBlocksKitSerializer
    # permission_classes = [AllowAnyCreate]
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

    # def get(self, request, *args, **kwargs):
    #     return Response({"message": "ok"}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer: BaseBlocksKitSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    




