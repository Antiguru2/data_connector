from rest_framework import serializers

from site_pages.models import SitePage
from html_constructor.models import (
    BaseBlocksKit,
    BaseHTMLBlock,
    NestedBaseHTMLBlock,
    TextItem,
)


class TextItemSerializer(serializers.Serializer):
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 

    value = serializers.CharField(required=False)

    class Meta:
        model = TextItem
        fields = [
            'base_html_block',
            'name',
            'slug',
            'description',
            'value',
        ]


class BaseContextItemSerializer(serializers.Serializer):
    value = serializers.CharField(
        required=False, source='default_value'
    )

    class Meta:
        # model = BaseContextItem
        fields = [
            'name',
            'slug',
            'value',
        ]
    
    
class BaseHTMLBlockSerializer(serializers.ModelSerializer):
    template_body = serializers.SerializerMethodField()  
    context_items = serializers.SerializerMethodField()  
    base_blocks_kit = serializers.SerializerMethodField()  

    class Meta:
        model = BaseHTMLBlock
        fields = [
            'template_name',
            'name',
            'slug',

            'template_body',
            'context_items',
            'base_blocks_kit',
        ]

    def get_template_body(self, obj):
        template_body = ''
        if obj.id:
            template_body = obj.template_body()
        return template_body
    
    def get_context_items(self, obj):
        base_context_items_data = []
        if obj.id and obj.base_context_items.exists():
            base_context_items_data = BaseContextItemSerializer(obj.base_context_items.filter(
                is_file=False,
                django_class=None,
            ), many=True).data
        return base_context_items_data
    
    def get_base_blocks_kit(self, obj):
        return {
            'name': 'Ли авто',
            'slug': 'li_auto',
        }
