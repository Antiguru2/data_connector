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
    Group,
)


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


class BaseBlocksKitSerializer(serializers.ModelSerializer):

    class Meta:
        model = BaseBlocksKit
        fields = [
            'name', 
            'slug', 
        ]


class NestedBaseHTMLBlockSerializer(serializers.ModelSerializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 
    description = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True, source='description'
    )
    nested_base_html_block = serializers.DictField(

    )

    class Meta:
        model = NestedBaseHTMLBlock
        fields = [
            'base_html_block',
            'name',
            'slug',
            'description',
            'order',

            'count',
            'nested_base_html_block',
        ]
    
    def create(self, validated_data):
        nested_block = None
        nested_base_html_block_data = validated_data.pop('nested_base_html_block', {})

        if nested_base_html_block_data:
            nested_blocks_serializer = BaseHTMLBlockSerializer(data=nested_base_html_block_data)
            if nested_blocks_serializer.is_valid():
                nested_block = nested_blocks_serializer.save()
            else:
                print('serializer.errors', nested_blocks_serializer.errors)      

        nested_base_html_block_model: NestedBaseHTMLBlock = super().create(validated_data)
        nested_base_html_block_model.nested_base_html_block = nested_block
        nested_base_html_block_model.save()

        return nested_base_html_block_model


class TextItemSerializer(serializers.ModelSerializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 
    description = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True, source='description'
    )

    class Meta:
        model = TextItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'description',
            'order',

            'value',
        ]


class FileItemSerializer(serializers.ModelSerializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 
    description = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True, source='description'
    )
    default_file = serializers.CharField(
        required=False, allow_null=True,
    )

    class Meta:
        model = FileItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'description',
            'order',

            'default_file',
        ]
    
    def create(self, validated_data):
        str_file = validated_data.pop('default_file', {})
        file_item: FileItem = super().create(validated_data)
        print('file_item', file_item)

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


class QuerysetItemSerializer(serializers.ModelSerializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 
    description = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True, source='description'
    )
    django_class = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True,
    )

    class Meta:
        model = QuerysetItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'description',
            'order',

            'django_class',
        ]

    def get_django_class(self, obj: QuerysetItem):
        if obj.django_class:
            return f"{obj.django_class.app_label}.{obj.django_class.model}"
        return None
    
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


class GroupSerializer(serializers.ModelSerializer):
    description = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True, source='description'
    )

    class Meta:
        model = Group
        fields = [
            'name',
            'slug',
            'description',
            'order',
        ]


class BaseHTMLBlockSerializer(serializers.ModelSerializer):
    description = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True, source='description'
    )
    template_body = serializers.CharField(
        required=False, allow_null=True, 
        allow_blank=True
    )
    groups = serializers.SlugRelatedField(
        queryset=Group.objects.all(),
        slug_field='slug',  # Укажите поле slug
        # required=False,
        many=True,
    )

    nested_blocks = NestedBaseHTMLBlockSerializer(
        many=True, 
        required=False,
        allow_null=True,
        allow_empty=True,
        # source='htmlblockitem_set',
    )  
    text_items = TextItemSerializer(
        many=True, 
        required=False,
        allow_null=True,
        allow_empty=True,
        # source='textitem_set',
    )  
    file_items = FileItemSerializer(
        many=True, 
        required=False,
        allow_null=True,
        allow_empty=True,
        # source='fileitem_set',
    )  
    queryset_items = QuerysetItemSerializer(
        many=True, 
        required=False,
        allow_null=True,
        allow_empty=True,
        # source='querysetitem_set',
    )  

    class Meta:
        model = BaseHTMLBlock
        fields = [
            'name',
            'slug',
            'description',
            'order',

            'template_body',

            'groups',
            'nested_blocks',
            'text_items',
            'file_items',
            'queryset_items',
        ]

    def create(self, validated_data):
        # print('BaseHTMLBlockSerializer.create()')
        # print('validated_data', validated_data)
        groups_data = validated_data.pop('groups', [])
        nested_blocks_data = validated_data.pop('nested_blocks', [])
        text_items_data = validated_data.pop('text_items', [])
        file_items_data = validated_data.pop('file_items', [])
        queryset_items_data = validated_data.pop('queryset_items', [])
        template_body = validated_data.pop('template_body', {})

        base_html_block: BaseHTMLBlock = BaseHTMLBlock.objects.create(**validated_data)
        # print('base_html_block', base_html_block)
        base_html_block.set_html_to_file(template_body)
        # print('validated_data', validated_data)

        base_html_block.groups.set(groups_data)

        for text_item_data in text_items_data:
            text_item_data['base_html_block'] = base_html_block.id
            text_items_serializer = TextItemSerializer(data=text_item_data)
            if text_items_serializer.is_valid():
                text_item = text_items_serializer.save()
            else:
                print('serializer.errors', text_items_serializer.errors)

        for file_item_data in file_items_data:
            file_item_data['base_html_block'] = base_html_block.id
            file_items_serializer = FileItemSerializer(data=file_item_data)
            if file_items_serializer.is_valid():
                file_item = file_items_serializer.save()
            else:
                print('serializer.errors', text_items_serializer.errors)

        for queryset_item_data in queryset_items_data:
            queryset_item_data['base_html_block'] = base_html_block.id
            queryset_item_serializer = QuerysetItemSerializer(data=queryset_item_data)
            if queryset_item_serializer.is_valid():
                queryset_item = queryset_item_serializer.save()
            else:
                print('serializer.errors', queryset_item_serializer.errors)

        for nested_block_data in nested_blocks_data:
            nested_block_data['base_html_block'] = base_html_block.id
            nested_block_serializer = NestedBaseHTMLBlockSerializer(data=nested_block_data)
            if nested_block_serializer.is_valid():
                nested_block = nested_block_serializer.save()
            else:
                print('serializer.errors', queryset_item_serializer.errors)

        return base_html_block
