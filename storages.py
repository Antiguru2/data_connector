# import os

# from django.conf import settings
# from django.core.signals import setting_changed
# from django.core.files.storage import FileSystemStorage

# from html_constructor.module_settings import (
#     PATH_TO_DEFAULT_FILES,
#     URL_TO_DEFAULT_FILES,
# )

# STATIC_URL = getattr(settings, 'STATIC_URL', '/static/')


# class SubModuleStaticStorage(FileSystemStorage):
#     '''
#         Данный класс не разширяет FileSystemStorage а просто устанавливает настройки хранилища
#         Если хотите то можно их указать при инициализации

#         Создано 23.05.2024 - Что бы не забыть
#     '''
#     def __init__(self, location=None, base_url=None, file_permissions_mode=None,
#                 directory_permissions_mode=None):
#         '''
#             Метод __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None):
#                 - Этот метод инициализирует объект FileSystemStorage с переданными параметрами.
#                 - location: Путь к корневой папке хранилища. default = settings.MEDIA_ROOT
#                 - base_url: Базовый URL для доступа к файлам. default = settings.MEDIA_URL 
#                 - file_permissions_mode: Режим разрешений для файлов.
#                 - directory_permissions_mode: Режим разрешений для директорий.
#         '''
#         self._location = PATH_TO_DEFAULT_FILES
#         self._base_url = URL_TO_DEFAULT_FILES
#         self._file_permissions_mode = file_permissions_mode
#         self._directory_permissions_mode = directory_permissions_mode
#         setting_changed.connect(self._clear_cached_properties)