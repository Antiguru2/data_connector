# import base64

# from rest_framework import serializers

# from site_pages.models import SitePage
# from html_constructor.models import (
#     # BaseBlocksKit,
#     BaseHTMLBlock,
#     # NestedBaseHTMLBlock,
#     BaseContextItem,
# )


# class BaseContextItemSerializer(serializers.ModelSerializer):
#     value = serializers.CharField(
#         required=False, source='default_value'
#     )
#     file = serializers.SerializerMethodField()    
#     django_class = serializers.SerializerMethodField() 

#     class Meta:
#         model = BaseContextItem
#         fields = [
#             'name',
#             'slug',
#             'value',
#             'is_file',
#             'file',
#             'django_class',
#         ]

#     def get_file(self, obj: BaseContextItem):
#         file = None
#         if obj.is_file and obj.default_file:
#             with obj.default_file.open() as f:
#                 file = f.read()  
#                 file = base64.b64encode(file).decode('utf-8')         

#         return file
    
#     def get_django_class(self, obj: BaseContextItem):
#         django_class = None
#         if obj.django_class:
#             django_class = f"{obj.django_class.app_label}.{obj.django_class.model}"
#         return django_class

    


# # class BaseContextItemSerializer(serializers.Serializer):
# #     value = serializers.CharField(
# #         required=False, source='default_value'
# #     )

# #     class Meta:
# #         # model = BaseContextItem
# #         fields = [
# #             'name',
# #             'slug',
# #             'value',
# #         ]
    
    
# class BaseHTMLBlockSerializer(serializers.ModelSerializer):
#     template_body = serializers.SerializerMethodField()  
#     context_items = serializers.SerializerMethodField()  

#     class Meta:
#         model = BaseHTMLBlock
#         fields = [
#             'template_name',
#             'name',
#             'slug',

#             'template_body',
#             'context_items',
#         ]

#     def get_template_body(self, obj):
#         template_body = ''
#         if obj.id:
#             template_body = obj.get_template_body()
#         return template_body
    
#     def get_context_items(self, obj):
#         base_context_items_data = []
#         if obj.id and obj.base_context_items.exists():
#             base_context_items = obj.base_context_items.all()
#             base_context_items_data = BaseContextItemSerializer(base_context_items, many=True).data
#         return base_context_items_data
    
