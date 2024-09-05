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


class ContextItemSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    slug = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    base_html_block = serializers.PrimaryKeyRelatedField(
        queryset=BaseHTMLBlock.objects.all(),
        required=False,
    ) 

    value = serializers.CharField(required=False)

    def create(self, validated_data):
        context_item = None
        value = validated_data.get('value', None)
        if value:
            serializer = TextItemSerializer(data=validated_data)    
            if serializer.is_valid():
                context_item = serializer.save()

        return context_item
    

# class NestedBaseHTMLBlockSerializer(serializers.ModelSerializer):
#     base_html_block = serializers.PrimaryKeyRelatedField(
#         queryset=BaseHTMLBlock.objects.all(),
#         required=False,
#     )  

#     class Meta:
#         model = NestedBaseHTMLBlock
#         fields = [
#             'slug',
#             'description',
#             'value',
#             'base_html_block',
#         ]

#     def create(self, validated_data):
#         validated_data['is_generated'] = True
#         return super().create(validated_data)
    

class BaseHTMLBlockSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(required=False)
    template_body = serializers.CharField(required=False)   
    context_items = ContextItemSerializer(many=True)
    # nested_blocks = NestedBaseHTMLBlockSerializer(many=True)

    class Meta:
        model = BaseHTMLBlock
        fields = [
            'name',
            'slug',
            'base_blocks_kit',
            'template_name',
            'template_body',
            'context_items',
            # 'nested_blocks',
        ]

    def create(self, validated_data):
        validated_data['template_name'] = ''

        context_items_data = validated_data.pop('context_items', {})
        nested_blocks_data = validated_data.pop('nested_blocks', {})

        template_body = validated_data.pop('template_body', {})

        base_html_block: BaseHTMLBlock = super().create(validated_data)
        base_html_block.set_html_to_file(template_body)

        if base_html_block:
            if context_items_data:

                for context_item_data in context_items_data:
                    context_item_data['base_html_block'] = base_html_block.id

                serializer = ContextItemSerializer(data=context_items_data, many=True)

                if serializer.is_valid():
                    context_items = serializer.save()

            # if nested_blocks_data:

            #     for nested_block_data in nested_blocks_data:
            #         nested_block_data['base_html_block'] = base_html_block.id

            #     serializer = NestedBaseHTMLBlockSerializer(data=nested_blocks_data, many=True)

            #     if serializer.is_valid():
            #         context_items = serializer.save()

        return base_html_block


class BaseBlocksKitSerializer(serializers.ModelSerializer):
    base_html_blocks = BaseHTMLBlockSerializer(many=True)

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

        return base_blocks_kit


