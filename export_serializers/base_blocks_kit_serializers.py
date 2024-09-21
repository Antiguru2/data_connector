import base64
import tempfile

from rest_framework import serializers

from django.apps import apps
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile

from site_pages.models import SitePage
from html_constructor.models import (
    BaseBlocksKit,
    BaseHTMLBlock,
    NestedBaseHTMLBlock,
    TextItem,
    FileItem,
    QuerysetItem,
)


class QuerysetItemSerializer(serializers.ModelSerializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 
    django_class = serializers.CharField(required=False, allow_null=True)  

    class Meta:
        model = QuerysetItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'django_class',
        ]

    def create(self, validated_data):
        app_model_string = validated_data.pop('django_class', {})
        if app_model_string:
            try:
                content_type: ContentType = ContentType.objects.get_by_natural_key(*app_model_string.split('.'))
            except ContentType.DoesNotExist:
                content_type = None
        validated_data['django_class'] = content_type
        queryset_item: FileItem = super().create(validated_data)

        return queryset_item


class TextItemSerializer(serializers.ModelSerializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 

    class Meta:
        model = TextItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'value',
        ]


class FileItemSerializer(serializers.ModelSerializer):
    file = serializers.CharField(required=False, allow_null=True)  

    class Meta:
        model = FileItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'file',
        ]

    def create(self, validated_data):
        str_file = validated_data.pop('file', {})
        file_item: FileItem = super().create(validated_data)

        if str_file:
            b_file = base64.b64decode(str_file)
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(b_file)
            content_file = ContentFile(b_file)
            file_name = f"{validated_data.get('slug')}.txt"
            in_memory_file = InMemoryUploadedFile(content_file, None, file_name, "text", content_file.tell(), None)
            file_item.default_file.save(file_name, in_memory_file)
            file_item.save()            

        return file_item
    

class ContextItemSerializer(serializers.Serializer):
    name = serializers.CharField(required=False) 
    slug = serializers.CharField(required=False) 
    value = serializers.CharField(required=False, allow_blank=True, allow_null=True) 
    file = serializers.CharField(required=False, allow_blank=True, allow_null=True) 
    is_file = serializers.BooleanField(required=False, allow_null=True) 
    django_class = serializers.CharField(required=False, allow_null=True) 

    class Meta:
        fields = [
            'name',
            'slug',
            'value',
            'file',
            'is_file',
            'django_class',
        ]



class BaseHTMLBlockSerializer(serializers.ModelSerializer): 
    template_body = serializers.CharField(required=False, allow_null=True, default='')   
    context_items = ContextItemSerializer(many=True, required=False)

    class Meta:
        model = BaseHTMLBlock
        fields = [
            'name',
            'slug',
            'base_blocks_kit',
            'template_body',
            'context_items',
        ]

    def create(self, validated_data):

        context_items_data = validated_data.pop('context_items', {})
        nested_blocks_data = validated_data.pop('nested_blocks', {})

        template_body = validated_data.pop('template_body', {})

        base_html_block: BaseHTMLBlock = super().create(validated_data)
        base_html_block.set_html_to_file(template_body)

        if base_html_block:
            for context_item_data in context_items_data:
                serializer = None
                context_item_data['base_html_block'] = base_html_block.id

                is_file = context_item_data.pop('is_file', False)
                if is_file:
                    serializer = FileItemSerializer(data=context_item_data)

                elif context_item_data.get('django_class'):
                    serializer = QuerysetItemSerializer(data=context_item_data)

                else:
                    serializer = TextItemSerializer(data=context_item_data)

                if serializer:
                    if serializer.is_valid():
                        context_item = serializer.save()
                    else:
                        print('serializer.errors', serializer.errors)
                else:
                    print('not serializer')

        return base_html_block


class BaseBlocksKitSerializer(serializers.ModelSerializer):
    base_html_blocks = BaseHTMLBlockSerializer(many=True, required=False)

    class Meta:
        model = BaseBlocksKit
        fields = [
            'name', 
            'slug', 
            'base_html_blocks',
        ]

    def create(self, validated_data):
        base_html_blocks_data = validated_data.pop('base_html_blocks', {})

        base_blocks_kit: BaseBlocksKit = super().create(validated_data)

        if base_html_blocks_data:

            for base_html_block_data in base_html_blocks_data:
                base_html_block_data['base_blocks_kit'] = base_blocks_kit.id

            serializer = BaseHTMLBlockSerializer(data=base_html_blocks_data, many=True)

            if serializer.is_valid():
                html_blocks = serializer.save()
            else:
                print('serializer.errors', serializer.errors)

        return base_blocks_kit


