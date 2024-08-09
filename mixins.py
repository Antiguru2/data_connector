# # from django.contrib.contenttypes.fields import GenericRelation

# from main.utils import (
#     get_model_by_name,
# )


# # class HTMLConstruktorMixin:
# #     """
# #     """
# #     tags = GenericRelation(HTMLConstruktor, related_query_name="bookmark")
# #     @classmethod
# #     def get_app_label(self):
# #         return self._meta.app_label
    
# #     def get_absolute_url(self):
# #         absolute_url = f"/{self._meta.app_label}/{self.slug}/"
# #         return absolute_url


# class ContextItemMixin:
#     """
#         Миксин предоставляющий методы для манипуляций с элементами контекста
#     """
#     def get_context_items_models(self) -> list:
#         """
#             Возвращает список всех моделей элементов контекста
#         """
#         context_items_models = []
#         context_items_classes = ContextItem.__subclasses__()
#         for context_items_class in context_items_classes:
#             context_items = getattr(self, f'{context_items_class.__name__.lower()}_set').all()
#             for context_item in context_items:
#                 context_items_models.append(context_item)

#         return context_items_models