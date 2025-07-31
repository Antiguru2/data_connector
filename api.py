import json

from urllib.parse import unquote

from django.views import View
from django.http import JsonResponse
from django.http.request import QueryDict
from django.core.exceptions import FieldError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType

from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import status, permissions

from .models import (
    DataConnector,
)


class SuperApiView(APIView):
    """
    Универсальный API-представление для работы с любыми моделями Django.
    
    Этот класс предоставляет стандартные CRUD-операции для любой модели Django через REST API.
    Поддерживает работу с различными типами данных и сериализаторами.
    
    Attributes:
        permission_classes (list): Список классов разрешений. По умолчанию требует аутентификации.
    """
    permission_classes = [
        # permissions.AllowAny, 
        permissions.IsAuthenticated, 
    ]

    def get_some_model(self, natural_key):
        """
        Получает класс модели по её натуральному ключу.
        
        Args:
            natural_key (str): Натуральный ключ модели в формате 'app_label.model_name'
            
        Returns:
            Model: Класс модели или None, если модель не найдена
        """
        try:
            separator = '__' if '__' in natural_key else '.'
            content_type = ContentType.objects.get_by_natural_key(*natural_key.split(separator))
            some_model = content_type.model_class()
        except:
            some_model = None


        return some_model
    
    def get_object(self, some_model, obj_id=None):
        """
        Получает объект модели по его ID.
        
        Args:
            some_model (Model): Класс модели
            obj_id (int, optional): ID объекта
            
        Returns:
            Model: Объект модели или None, если объект не найден
        """
        if not obj_id:
            return None
        
        return some_model.objects.filter(id=obj_id).first()
    
    def get_queryset(self, some_model, obj_id=None, get_params={}):
        """
        Формирует QuerySet для модели с учетом фильтров.
        
        Args:
            some_model (Model): Класс модели
            obj_id (int, optional): ID объекта
            get_params (dict): Параметры фильтрации из GET-запроса
            
        Returns:
            QuerySet: Отфильтрованный набор объектов
        """
        if obj_id:
            return some_model.objects.filter(id=obj_id)
        elif get_params:
            return some_model.objects.filter(**self.get_django_filter(get_params))
        else:
            return some_model.objects.all()
        
    def get_request_data(self, request):
        """
        Извлекает данные из запроса в различных форматах.
        
        Args:
            request (Request): Объект запроса
            
        Returns:
            dict: Данные запроса
        """
        request_data = {}
        if request.body:
            request_data = json.loads(request.body)
        
        if not request_data and request.data:
            request_data = request.data

        if not request_data and request.POST:
            request_data = request.POST
        
        return request_data

    def get_django_filter(self, get_params: QueryDict) -> dict:
        """
        Преобразует параметры GET-запроса в фильтры Django ORM.
        
        Args:
            get_params (QueryDict): Параметры GET-запроса
            
        Returns:
            dict: Словарь фильтров для Django ORM
        """
        django_filter = {}

        for get_param_slug, get_param_value in get_params.items():

            # print('get_param_value', get_param_value)
            # Пробразуем спецефичные для QueryDict значения в валидные значения для objects.filter()
            if get_param_value in ['True', 'true', 'False', 'false']:
                if get_param_value in ['True', 'true']:
                    get_param_value = True
                else:
                    get_param_value = False
            else:
                if ',' in get_param_value:
                    get_params_value = get_param_value.split(',')
                    get_param_value = []
                    for get_params_value_item in get_params_value:
                        try:
                            get_param_value.append(int(get_params_value_item))
                        except ValueError:
                            get_param_value.append(unquote(get_params_value_item))

            if type(get_param_value) not in [list, bool]:
                try:
                    get_param_value = int(get_param_value)
                except ValueError:
                    pass

            try:
                django_filter[get_param_slug] = get_param_value
            except AttributeError:
                pass
            except FieldError:
                pass

        return django_filter
    
    def get_arg(self, arg):
        """
        Обрабатывает аргумент, преобразуя специальные значения в None.
        
        Args:
            arg: Входной аргумент
            
        Returns:
            any: Обработанный аргумент
        """
        if arg in ['none', 0]:
            arg = None
        return arg
        
    def get(self, request, natural_key, obj_id=None, data_type='rest', serializer_name=None):
        """
        Обрабатывает GET-запрос для получения данных.
        
        Args:
            request (Request): Объект запроса
            natural_key (str): Натуральный ключ модели
            obj_id (int, optional): ID объекта
            data_type (str, optional): Тип данных ('rest' или 'form')
            serializer_name (str, optional): Имя сериализатора
            
        Returns:
            Response: Ответ с данными или сообщением об ошибке
        """
        obj_id = self.get_arg(obj_id)
        serializer_name = self.get_arg(serializer_name)

        data_type = self.get_arg(data_type)
        if data_type and data_type not in ['rest', 'form', 'key-form'] :
            return Response({"status": "error", "message": "Такой тип данных не обрабатывается, используйте 'rest' или 'form'"}, status=status.HTTP_404_NOT_FOUND)

        some_model = self.get_some_model(natural_key)
        if not some_model:
            return Response({"status": "error", "message": "Нет модели с таким натуральным ключом"}, status=status.HTTP_404_NOT_FOUND)
        
        
        if obj_id:
            obj = self.get_object(some_model, obj_id)

            if not obj:
                return Response({"status": "error", "message": "Нет объекта с таким id"}, status=status.HTTP_404_NOT_FOUND)
            
        queryset = self.get_queryset(some_model, obj_id, request.GET)

        if not queryset:
            return Response({"status": "ok", "message": "Не найдено ни одного обьекта", "data": [],}, status=status.HTTP_200_OK)

        try:
            serializer = DataConnector.get_serializer(some_model, user=request.user, data_type=data_type, serializer_name=serializer_name)
        except:
            serializer = None

        if not serializer:
            return Response({"status": "error", "message": "У модели нет сериализатора"}, status=status.HTTP_404_NOT_FOUND)
        
        has_permission = serializer.has_permission(request.user, queryset)
        if not has_permission:
            return Response({"status": "error", "message": "У пользователя нет прав на просмотр данных"}, status=status.HTTP_403_FORBIDDEN)
        
        data = serializer.get_data(queryset)

        if not data:
            return Response({"status": "error", "message": "Нет данных"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"status": "ok", "message": "", "data": data}, status=status.HTTP_200_OK)
    
    # @csrf_exempt
    def post(self, request, natural_key, obj_id=None, data_type='rest', serializer_name=None):
        """
        Обрабатывает POST-запрос для создания нового объекта.
        
        Args:
            request (Request): Объект запроса
            natural_key (str): Натуральный ключ модели
            obj_id (int, optional): ID объекта (не используется при создании)
            data_type (str, optional): Тип данных
            serializer_name (str, optional): Имя сериализатора
            
        Returns:
            JsonResponse: Ответ с результатом создания или сообщением об ошибке
        """
        if obj_id:   
            return JsonResponse({"message": "Нельзя задать id для создаваемого обьекта"}, status=status.HTTP_404_NOT_FOUND)

        request_data = self.get_request_data(request)
        # print('request_data', request_data)

        if not request_data:
            return JsonResponse({"message": "Данные не найдены"}, status=status.HTTP_404_NOT_FOUND)

        # data = request_data.get('data')
        # if not data:
        #     return Response({"message": "Данные не найдены"}, status=status.HTTP_404_NOT_FOUND)

        some_model = self.get_some_model(natural_key)
        if not some_model:
            return JsonResponse({"message": "Нет модели с таким натуральным ключом"}, status=status.HTTP_404_NOT_FOUND)

        serializer_self_assembly_data = None
        if type(request_data) == dict:
            serializer_self_assembly_data = request_data.get('serializer_self_assembly_data')

        try:
            serializer = DataConnector.get_serializer(
                some_model,
                user=request.user,
                serializer_name=serializer_name, 
                serializer_self_assembly_data=serializer_self_assembly_data,
            )
        except:
            serializer = None

        if not serializer:
            return JsonResponse({"message": "Сериализатор не найден"}, status=status.HTTP_404_NOT_FOUND)       

        comment, response_status, response_data = serializer.set_data(request_data, method='create') 

        return JsonResponse(
            {
                "message": comment,
                "data": response_data,
            }, 
            status=response_status,
        )
    

    def patch(self, request, natural_key, obj_id=None, data_type='rest', serializer_name=None):
        """
        Обрабатывает PATCH-запрос для частичного обновления объекта.
        
        Args:
            request (Request): Объект запроса
            natural_key (str): Натуральный ключ модели
            obj_id (int): ID обновляемого объекта
            data_type (str, optional): Тип данных
            serializer_name (str, optional): Имя сериализатора
            
        Returns:
            JsonResponse: Ответ с результатом обновления или сообщением об ошибке
        """
        if not obj_id:   
            return JsonResponse({"message": "В url не задан id для обновляемого обьекта"}, status=status.HTTP_404_NOT_FOUND)

        request_data = self.get_request_data(request)

        if not request_data:
            return JsonResponse({"message": "Данные не найдены"}, status=status.HTTP_404_NOT_FOUND)

        # data = request_data.get('data')
        # if not data:
        #     return Response({"message": "Данные не найдены"}, status=status.HTTP_404_NOT_FOUND)

        some_model = self.get_some_model(natural_key)
        if not some_model:
            return JsonResponse({"message": "Нет модели с таким натуральным ключом"}, status=status.HTTP_404_NOT_FOUND)

        serializer_self_assembly_data = None
        if type(request_data) == dict:
            serializer_self_assembly_data = request_data.get('serializer_self_assembly_data')

        try:
            serializer = DataConnector.get_serializer(
                some_model,
                user=request.user,
                serializer_name=serializer_name, 
                serializer_self_assembly_data=serializer_self_assembly_data,
            )
        except:
            serializer = None

        if not serializer:
            return JsonResponse({"message": "Сериализатор не найден"}, status=status.HTTP_404_NOT_FOUND)       

        comment, response_status, response_data = serializer.set_data(request_data, obj_id=obj_id) 

        return JsonResponse(
            {
                "message": comment,
                "data": response_data,
            }, 
            status=response_status,
        )
    
    def put(self, request, natural_key, obj_id=None, data_type='rest', serializer_name=None):
        """
        Обрабатывает PUT-запрос (не реализовано).
        
        Returns:
            JsonResponse: Сообщение о том, что метод не найден
        """
        return JsonResponse({"message": "method not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, natural_key, obj_id=None, data_type='rest', serializer_name=None):
        """
        Обрабатывает DELETE-запрос (не реализовано).
        
        Returns:
            JsonResponse: Сообщение о том, что метод не найден
        """
        return JsonResponse({"message": "method not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def options(self, request, natural_key, obj_id=None, data_type='rest', serializer_name=None):
        """
        Обрабатывает OPTIONS-запрос для получения структуры сериализатора.
        
        Args:
            request (Request): Объект запроса
            natural_key (str): Натуральный ключ модели
            obj_id (int, optional): ID объекта
            data_type (str, optional): Тип данных
            serializer_name (str, optional): Имя сериализатора
            
        Returns:
            Response: Структура сериализатора с пустыми значениями
        """
        some_model = self.get_some_model(natural_key)
        if not some_model:
            return Response({"status": "error", "message": "Нет модели с таким натуральным ключом"}, status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = DataConnector.get_serializer(
                some_model,
                user=request.user,
                data_type=data_type,
                serializer_name=serializer_name
            )
        except:
            serializer = None

        if not serializer:
            return Response({"status": "error", "message": "У модели нет сериализатора"}, status=status.HTTP_404_NOT_FOUND)

        # Получаем структуру с пустыми значениями
        structure = serializer.get_structure()

        return Response({
            "status": "ok",
            "message": "",
            "data": structure
        }, status=status.HTTP_200_OK)

