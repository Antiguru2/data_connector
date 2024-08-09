# import os

# from django.conf import settings
# from django.dispatch import receiver
# from django.db.models.signals import (
#     pre_delete, 
#     pre_save,
#     post_save,
#     post_delete,
#     post_migrate,
# )
# from django.db.utils import OperationalError

# from html_constructor.models import (
#     BaseHTMLBlock,
#     HTMLBlock,
#     Group,
#     ContextItem,
#     FileItem,
#     HTMLBlockItem,
# )
# from html_constructor.module_settings import (
#     DEFAULT_GROUP_NAME,
#     DEFAULT_GROUP_SLUG,
# )
# from html_constructor.storages import (
#     SubModuleStaticStorage,
# )
# from main.utils import (
#     is_model_fields_changes,
# )
# # from main.models import SitePreferences

# # BASE_DIR = getattr(settings, 'BASE_DIR')


# base_groups_dict = {
#     DEFAULT_GROUP_NAME: DEFAULT_GROUP_SLUG,
#     'Вложеный': 'nested',
# }


# @receiver(post_migrate)
# def create_base_groups(sender, **kwargs):
#     '''
#         При миграции астоматически создаются базовые группы
#     '''
#     if sender.name == 'html_constructor':
#         for name, slug in base_groups_dict.items():
#             Group.objects.get_or_create(
#                 name=name,
#                 slug=slug,
#             )


# @receiver(post_save, sender=BaseHTMLBlock)
# def create_default_values_for_content_items(
#     sender: BaseHTMLBlock, 
#     instance: BaseHTMLBlock, 
#     created: bool, 
#     **kwargs
# ):
#     '''
#         Если блок создается без группы то он автоматически привязывается к основной группе
#     '''
#     if created and not instance.groups.exists():
#         default_group = Group.objects.get(slug=DEFAULT_GROUP_SLUG)
#         default_group.base_html_blocks.add(instance)


# @receiver(pre_save, sender=HTMLBlockItem)
# def create_nested_html_blocks(
#     sender: HTMLBlockItem, 
#     instance: HTMLBlockItem, 
#     **kwargs
# ):
#     is_changes = is_model_fields_changes(sender, instance, ['nested_html_block',])

#     old_instance = sender.objects.filter(id=instance.id).first()
#     if is_changes and old_instance and old_instance.nested_html_block:
#         html_blocks = instance.base_html_block.html_blocks.all()
#         for html_block in html_blocks:
#             html_block_items = HTMLBlockItem.objects.filter(
#                 html_block=html_block,
#             )
#             for html_block_item in html_block_items:
#                 html_block_item.html_blocks.all().delete()

#     if is_changes and instance.nested_html_block and instance.count:
#         html_blocks = instance.base_html_block.html_blocks.all()
#         for html_block in html_blocks:
#             html_block_item, created = HTMLBlockItem.objects.get_or_create(
#                 name=instance.name,
#                 slug=instance.slug,
#                 html_block=html_block,
#             )

#             for n in range(instance.count):
#                 new_html_block = HTMLBlock.objects.create(
#                     base_html_block=instance.nested_html_block,
#                     order=n,
#                 )
#                 new_html_block.add_content_items()
#                 html_block_item.html_blocks.add(new_html_block)


# @receiver(post_delete, sender=HTMLBlockItem)
# def reaction_base_context_item_delete(
#     sender: HTMLBlockItem, 
#     instance: HTMLBlockItem, 
#     **kwargs
# ):  
#     if instance.base_html_block:
#         html_blocks = instance.base_html_block.html_blocks.all()

#         for html_block in html_blocks:
#             HTMLBlockItem.objects.filter(
#                 html_block=html_block,
#             ).delete()






# # @receiver(pre_save, sender=html_constructor_models.BaseContextItem)
# # def update_is_file(
# #     sender: html_constructor_models.BaseContextItem, 
# #     instance: html_constructor_models.BaseContextItem, 
# #     **kwargs
# # ):
# #     if instance.default_file:
# #         instance.is_file = True

# #     if instance.id:
# #         try:
# #             old_image = sender.objects.get(id=instance.id).default_file
# #         except sender.DoesNotExist:
# #             return
        
# #         new_image = instance.default_file
# #         if old_image and old_image != new_image:
# #             site_preferences = SitePreferences.get_model()
# #             if site_preferences:
# #                 if site_preferences.delete_img_in_dir:
# #                     old_image.delete(False)
# #             else:
# #                 old_image.delete(False)  


# # @receiver(post_save, sender=html_constructor_models.HTMLBlock)
# # def create_default_values_for_content_items(sender, instance, created, **kwargs):
# #     if created and instance and instance.base_html_block:

# #         base_context_items = instance.base_html_block.base_context_items.all()
# #         for base_context_item in base_context_items:
# #                 if base_context_item.is_file:
# #                     html_constructor_models.ContextFile.objects.get_or_create(
# #                         html_block=instance,
# #                         base_context_item=base_context_item,
# #                         name=base_context_item.name
# #                     )

# #                 if base_context_item.django_class:
# #                         html_constructor_models.ContextObjects.objects.get_or_create(
# #                         html_block=instance,
# #                         base_context_item=base_context_item,
# #                         name=base_context_item.name,
# #                     )

# #                 if not base_context_item.is_file and not base_context_item.django_class:
# #                     html_constructor_models.ContextItem.objects.get_or_create(
# #                         html_block=instance,
# #                         base_context_item=base_context_item,
# #                         name=base_context_item.name,
# #                         value=base_context_item.default_value,
# #                     )


# # @receiver(post_save, sender=html_constructor_models.BaseContextItem)
# # def reaction_to_create(
# #     sender: html_constructor_models.BaseContextItem, 
# #     instance: html_constructor_models.BaseContextItem, 
# #     created, 
# #     **kwargs
# # ):
# #     if created:
# #         instance.create_context_items()


# # @receiver(pre_save, sender=html_constructor_models.BaseContextItem)
# # def reaction_to_change(
# #     sender: html_constructor_models.BaseContextItem, 
# #     instance: html_constructor_models.BaseContextItem, 
# #     **kwargs
# # ):
# #     if instance.default_file:
# #         instance.is_file = True
        
# #     if instance.id:
# #         is_changes = is_model_fields_changes(sender, instance, ['is_file', 'django_class'])
# #         if is_changes:          
# #             instance.delete_context_items()
# #             instance.create_context_items()


# # @receiver(post_delete, sender=html_constructor_models.BaseContextItem)
# # def reaction_base_context_item_delete(
# #     sender: html_constructor_models.BaseContextItem, 
# #     instance: html_constructor_models.BaseContextItem, 
# #     **kwargs
# # ):  
# #     instance.delete_context_items()

 


# # Пресейверы для ContextItem`s всех типов
# try:
#     SomeImageModels = ContextItem.__subclasses__()

#     for SomeImageModel in SomeImageModels:
#         @receiver(pre_save, sender=SomeImageModel)
#         def set_base_context_item_for_context_item(sender, instance,**kwargs):
#             if hasattr(instance, 'html_block') and instance.html_block:
#                 base_html_block = instance.html_block.base_html_block

#                 context_items_models = base_html_block.get_context_items_models()
#                 for context_items_model in context_items_models:
#                     if context_items_model.slug == instance.slug:
#                         instance.base_context_item = context_items_model

#             # if hasattr(instance, 'base_html_block'):
#             #     base_html_block = instance.base_html_block

#             #     context_items_models = base_html_block.get_context_items_models()
#             #     for context_items_model in context_items_models:
#             #         if context_items_model.slug == instance.slug:


# except OperationalError:        
#     print('Ошибка в html_constructor.signals. Если ошибка произошла во время миграций то все норм.')    