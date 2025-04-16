import traceback

from typing import Optional

from django.db import models
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from .abstract_models import SerializerFieldAbstractModel, DataConnectorAbstractModel
from .field_handlers import *


class SerializerFieldMixin:
    """
    Миксин для добавления функциональности сериализации полей.
    
    Этот миксин предоставляет методы для работы с сериализацией полей модели.
    Он может быть использован как в классе SerializerField, так и в других классах,
    которым требуется аналогичная функциональность.
    
    Основные возможности:
    - Получение обработчиков полей (get_handler, get_input_handler, get_form_handler)
    - Работа со структурой данных (get_structure_handler)
    """
    def get_handler(self):
        """
        Возвращает обработчик поля для сериализации данных.
        
        Returns:
            FieldHandler: Обработчик поля, соответствующий типу поля.
        """
        handler_type = self.type_for_handler if self.type_for_handler else self.type  
        return FieldHandler(name=handler_type)
    
    def get_input_handler(self):
        """
        Возвращает обработчик для входящих данных.
        
        Returns:
            IncomingFieldHandler: Обработчик входящих данных.
        """
        handler_type = self.incoming_handler if self.incoming_handler else self.type
        return IncomingFieldHandler(name=handler_type)

    def get_form_handler(self):
        """
        Возвращает обработчик для работы с формами.
        
        Returns:
            FormFieldHandler: Обработчик форм.
        """
        handler_type = self.type_for_form_handler if self.type_for_form_handler else self.type
        return FormFieldHandler(name=handler_type)
    
    def get_structure_handler(self):
        """
        Возвращает обработчик для работы со структурой данных.
        
        Returns:
            StructureFieldHandler: Обработчик структуры данных.
        """
        return StructureFieldHandler(name=self.type)


class DataConnectorMixin:
    """
    Миксин для добавления функциональности сериализации данных.
    
    Этот миксин предоставляет методы для работы с сериализацией данных модели.
    Он может быть использован как в классе DataConnector, так и в других классах,
    которым требуется аналогичная функциональность.
    
    Основные возможности:
    - Получение и создание сериализаторов
    - Сериализация данных в различных форматах (REST, FORM)
    - Десериализация входящих данных
    - Работа со структурой данных
    - Управление полями сериализатора
    """
    @property
    @admin.display(description=_('Дополнительные кнопки'))
    def additional_buttons(self):
        """
        Возвращает HTML-код дополнительных кнопок для админки.
        
        Returns:
            str: HTML-код кнопок.
        """
        return self.get_additional_buttons()
    
    def get_additional_buttons(self):
        """
        Формирует HTML-код дополнительных кнопок.
        
        Returns:
            str: HTML-код кнопок.
        """
        additional_buttons = ''
        if self.content_type:
            model = self.content_type.model_class()
            additional_buttons += f"<a href='/data_connector/super-api/{model._meta.app_label}__{model.__name__.lower()}/'><button>К данным</button></a>"
        return mark_safe(additional_buttons)
    
    @classmethod
    def get_self_assembly(cls, data: Optional[dict] = None):
        """
        Метод для самосборки сериализатора из входящих данных.
        """
        self_assembly = None
        return self_assembly
    
    @classmethod
    def get_serializer(
        cls,
        some_model: models.Model,
        user: models.Model,
        method: str = 'GET',
        data_type: str = 'rest',
        serializer_name: Optional[str] = None, 
        serializer_self_assembly_data: Optional[dict] = None
    ):    
        """
        Получает или создает сериализатор для модели.
        
        Args:
            some_model (models.Model): Модель для сериализации.
            user (models.Model): Пользователь, запрашивающий сериализатор.
            method (str): HTTP-метод запроса.
            data_type (str): Тип данных (rest/form).
            serializer_name (Optional[str]): Имя сериализатора.
            serializer_self_assembly_data (Optional[dict]): Данные для автоматической настройки.
            
        Returns:
            DataConnector: Настроенный сериализатор.
        """
        serializer = None
        if serializer_self_assembly_data:
            serializer = cls.get_self_assembly(serializer_self_assembly_data)
        else:
            content_type = ContentType.objects.get_for_model(some_model)
            serializers = cls.objects.filter(content_type=content_type)
            
            if serializer_name:
                serializers = serializers.filter(name=serializer_name)

        if serializer and not serializer.is_active:
            serializer = None

        if not serializer:
            serializer = cls(
                content_type=content_type,
                is_active=True,
                is_allow_view=True,
                is_allow_edit=False,
                is_allow_delete=False,
                is_allow_create=False,
            )
            if user.is_superuser:
                serializer.is_allow_edit = True
                serializer.is_allow_delete = True
                serializer.is_allow_create = True

        serializer.method = method
        serializer.user = user
        serializer.data_type = data_type

        return serializer

    def set_data(self, request_data: dict, method: str, obj_id: Optional[int] = None):
        """
        Устанавливает данные через сериализатор.
        
        Args:
            request_data (dict): Входящие данные.
            method (str): HTTP-метод запроса.
            obj_id (Optional[int]): ID объекта для обновления.
            
        Returns:
            tuple: (комментарий, статус, данные)
        """
        comment = ''
        response_status = 200
        
        try:
            queryset = self.deserialize(request_data, method, obj_id)
        except Exception as error:
            queryset = self.content_type.model_class().objects.none()
            print('error', error)

        try:
            response_data = self.serialize(queryset)
        except Exception as error:
            response_data = {}
            print('error', error)

        return comment, response_status, response_data
    
    def get_data(self, queryset: models.QuerySet):
        """
        Получает сериализованные данные.
        
        Args:
            queryset (models.QuerySet): Набор объектов для сериализации.
            
        Returns:
            dict: Сериализованные данные.
        """
        response_data = {}
        try:
            response_data = self.serialize(queryset)
        except Exception as error:
            traceback.print_exc()
            print('get_data', error)

        return response_data

    def serialize(self, queryset: models.QuerySet, **kwargs):
        """
        Сериализует данные в зависимости от типа.
        
        Args:
            queryset (models.QuerySet): Набор объектов для сериализации.
            **kwargs: Дополнительные параметры.
            
        Returns:
            list: Сериализованные данные.
        """
        serializer_data = []
        if self.data_type == 'rest':
            serializer_data = self.serialize_rest_data(queryset, **kwargs)
        elif self.data_type == 'form':
            serializer_data = self.serialize_form_data(queryset, **kwargs)

        return serializer_data
    
    def serialize_rest_data(self, queryset: models.QuerySet, **kwargs):
        """
        Сериализует данные в REST формате.
        
        Args:
            queryset (models.QuerySet): Набор объектов для сериализации.
            **kwargs: Дополнительные параметры.
            
        Returns:
            list: Сериализованные данные в REST формате.
        """
        serializer_data = []
        for obj in queryset:
            fields_data = {}
            serializer_fields = self.get_serializer_fields()
            for serializer_field in serializer_fields:
                handler: FieldHandler = serializer_field.get_handler()
                if not handler:
                    value = 'Oбработчик не настроен'
                else:
                    serializer_field_name = serializer_field.name
                    if serializer_field.alt_key:
                        serializer_field_name = serializer_field.alt_key
                        
                    value = handler.get_value(obj, serializer_field)

                fields_data[serializer_field_name] = value

            if fields_data:
                serializer_data.append(fields_data)

        return serializer_data
    
    def serialize_form_data(self, queryset: models.QuerySet, **kwargs):
        """
        Сериализует данные в FORM формате.
        
        Args:
            queryset (models.QuerySet): Набор объектов для сериализации.
            **kwargs: Дополнительные параметры.
            
        Returns:
            list: Сериализованные данные в FORM формате.
        """
        serializer_data = []
        for obj in queryset:
            serializer_fields = self.get_serializer_fields()
            for serializer_field in serializer_fields:
                handler: FieldHandler = serializer_field.get_handler()
                if not handler:
                    value = 'Oбработчик не настроен'
                        
                value = handler.get_value(obj, serializer_field)

                form_handler = serializer_field.get_form_handler()
                serializer_data.append({
                    "name": serializer_field.name,
                    "verbose_name": serializer_field.verbose_name,
                    "type": serializer_field.type,
                    "value": value,
                })                

        return serializer_data

    def get_structure(self, additional_field_keys: list = ['description', 'examples', 'verbose_name']):
        """
        Получает структуру данных сериализатора.
        
        Returns:
            list: Структура данных.
        """
        serializer_data = []
        serializer_fields = self.get_serializer_fields()
        for serializer_field in serializer_fields:
            structure_handler = serializer_field.get_structure_handler()
            value = structure_handler.get_value(serializer_field)


            field_data = {
                "name": serializer_field.name,
                "type": serializer_field.type,
                "value": value,
            }
            
            for additional_field_key in additional_field_keys:
                print('additional_field_key', additional_field_key)
                print(serializer_field.__class__.__name__)
                # print(dir(serializer_field))
                print(hasattr(serializer_field, additional_field_key))
                if hasattr(serializer_field, additional_field_key):
                    serializer_field_value = getattr(serializer_field, additional_field_key)
                    field_data[additional_field_key] = serializer_field_value or ''

            print('default_field_data', field_data)
            serializer_data.append(field_data)                

        return serializer_data
    
    def deserialize(self, request_data, method: str, obj_id: Optional[int] = None):
        """
        Десериализует входящие данные.
        
        Args:
            request_data: Входящие данные.
            method (str): HTTP-метод запроса.
            obj_id (Optional[int]): ID объекта для обновления.
            
        Returns:
            QuerySet: Набор объектов после десериализации.
        """
        some_model_class = self.content_type.model_class()
        request_data_list = [request_data] if type(request_data) == dict else request_data
        serializer_fields = self.serializer_fields.filter(is_active=True).all()

        error_data = {}
        if obj_id:
            some_model = some_model_class.objects.get(id=obj_id)
        else:
            some_model = some_model_class()

        for request_data_dict in request_data_list:
            for field_name, field_value in request_data_dict.items():
                if field_name == 'id':
                    continue

                try:
                    serializer_field = serializer_fields.filter(name=field_name).first()
                    input_handler: FieldHandler = serializer_field.get_handler()
                    transform_field_name, transform_field_value, error = input_handler.get_transform_data(field_value, serializer_field)
                    setattr(some_model, transform_field_name, transform_field_value)
                except Exception as error:
                    print(f'DataConnector.deserialize() error in field {field_name}', error)
                finally:
                    error_data[field_name] = error

            some_model.save()
            
        queryset = some_model_class.objects.filter(id=some_model.id)
        return queryset

    def get_serializer_fields_class(self):
        """
        Возвращает класс полей сериализатора.
        """
        return self.serializer_fields.model

    def get_serializer_fields(self):
        """
        Получает поля сериализатора.
        
        Returns:
            QuerySet: Набор полей сериализатора.
        """
        try:
            serializer_fields = self.serializer_fields.filter(is_active=True).all()
            return serializer_fields
        except Exception as error:
            serializer_fields = []

        model = self.content_type.model_class()
        
        for model_field in model._meta.get_fields():
            field_type = model_field.__class__.__name__
            verbose_name = getattr(model_field, 'verbose_name', model_field.name)
            
            serializer_field = self.get_serializer_fields_class()(
                data_connector=self,
                verbose_name=verbose_name,
                name=model_field.name,
                type=field_type,
            )
            serializer_fields.append(serializer_field)
        
        return serializer_fields
