from pprint import pprint
from typing import Optional, Union

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

    def get_super_handler(self, data_type: str):
        """
        Возвращает обработчик поля для сериализации данных.
        """
        if data_type == 'key-form':
            return KeyFormFieldHandler(name=self.type)
        else:
            return None
    
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

    def get_validate_handler(self):
        """
        Возвращает обработчик для валидации данных.
        """
        return ValidateFieldHandler(name=self.type)


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
        data_type: str = 'rest',
        serializer_name: Optional[str] = None, 
        serializer_self_assembly_data: Optional[dict] = None
    ):    
        """
        Получает или создает сериализатор для модели.
        
        Args:
            some_model (models.Model): Модель для сериализации.
            user (models.Model): Пользователь, запрашивающий сериализатор.
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
            serializers = cls.objects.filter(
                content_type=content_type,
                is_active=True,
            )
            
            if serializer_name:
                serializer = serializers.get(slug=serializer_name)

            if not serializer and serializers.exists():
                serializer = serializers.first()

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

        serializer.user = user

        if not data_type:
            data_type = 'rest'        
        serializer.data_type = data_type

        return serializer
    
    def has_permission(self, user: models.Model, queryset: models.QuerySet) -> bool:
        """
        Проверяет, имеет ли пользователь право на просмотр данных.
        """
        return True

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
            queryset, error_data = self.deserialize(request_data, method, id_field_value=obj_id)
        except Exception as error:
            queryset = self.content_type.model_class().objects.none()
            print('DataConnectorMixin.set_data() error', error)

        try:
            response_data = self.serialize(queryset)
        except Exception as error:
            response_data = {}
            print('DataConnectorMixin.set_data() error', error)

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
            print('DataConnectorMixin.get_data() error', error)

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
        elif self.data_type == 'key-form':
            serializer_data = self.serialize_key_form_data(queryset, **kwargs)

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
            fields_data = []
            serializer_fields = self.get_serializer_fields()
            for serializer_field in serializer_fields:
                handler: FieldHandler = serializer_field.get_handler()
                if not handler:
                    value = 'Oбработчик не настроен'
                        
                value = handler.get_value(obj, serializer_field)
                fields_data.append({
                    "name": serializer_field.name,
                    "verbose_name": serializer_field.verbose_name,
                    "type": serializer_field.type,
                    "value": value,
                })   

            serializer_data.append(fields_data)

        return serializer_data
    
    def serialize_key_form_data(self, queryset: models.QuerySet, **kwargs):
        """
        Сериализует данные в KEY-FORM формате.
        """
        serializer_data = []
        for obj in queryset:
            fields_data = {}
            serializer_fields = self.get_serializer_fields()
            for serializer_field in serializer_fields:
                handler: FieldHandler = serializer_field.get_super_handler(data_type='key-form')
                if not handler:
                    value = 'Oбработчик не настроен'
                else:
                    value = handler.get_value(obj, serializer_field)

                fields_data[serializer_field.name] = {
                    'value': value,
                    'type': serializer_field.type,
                    'verbose_name': serializer_field.verbose_name,
                }

            serializer_data.append(fields_data)

        return serializer_data 

    def get_structure(self, **kwargs):
        """
        Получает структуру данных сериализатора.
        
        Returns:
            list: Структура данных.
        """
        serializer_data = []
        if self.data_type == 'rest':
            raise NotImplementedError('get_structure for rest data type is not implemented')
        elif self.data_type == 'form':
            serializer_data = self.get_form_structure(**kwargs)

        return serializer_data
    
    def validate(self, data: dict, **kwargs) -> tuple[bool, dict]:
        """
        Валидирует входящие данные.
        
        Args:
            data (dict): Данные для валидации
            **kwargs: Дополнительные параметры
            
        Returns:
            tuple[bool, dict]: (результат валидации, словарь с ошибками)
        """
        if self.data_type == 'rest':
            raise NotImplementedError('validate for rest data type is not implemented')
        elif self.data_type == 'form':
            return self.validate_form_data(data, **kwargs)
        
        return False, {'error': 'Неизвестный тип данных'}

    def validate_form_data(self, data: list, level: int = 0, **kwargs) -> tuple[bool, dict]:
        """
        Валидирует данные в формате FORM.
        
        Args:
            data (dict): Данные для валидации
            **kwargs: Дополнительные параметры
            
        Returns:
            tuple[bool, dict]: (результат валидации, словарь с исходными данными, дополненными информацией о валидации)
        """
        validate_data = []
        serializer_fields = self.get_serializer_fields()
        is_valid = True

        for n, field in enumerate(data):
            field_name = field.get('name')

            serializer_field = serializer_fields.filter(name=field_name).first()
            if not serializer_field:
                continue

            validate_handler = serializer_field.get_validate_handler()
            field_is_valid, validate_field_data = validate_handler.validate(field, serializer_field, level=level)
            if not field_is_valid and level == 0:
                validate_data.insert(0, validate_field_data)
            else:
                validate_data.append(validate_field_data)
                        
            if not field_is_valid:
                is_valid = False

        return is_valid, validate_data

    def get_form_structure(self, additional_field_keys: list = [], **kwargs):
        """
        Получает структуру данных сериализатора.
        
        Returns:
            list: Структура данных.
        """
        serializer_data = []
        serializer_fields = self.get_serializer_fields()
        for serializer_field in serializer_fields:
            structure_handler: StructureFieldHandler = serializer_field.get_structure_handler()
            value = structure_handler.get_value(serializer_field, additional_field_keys=additional_field_keys)


            field_data = {
                "name": serializer_field.name,
                "type": serializer_field.type,
                "value": value,
            }
            
            for additional_field_key in additional_field_keys:
                if hasattr(serializer_field, additional_field_key):
                    serializer_field_value = getattr(serializer_field, additional_field_key)
                    field_data[additional_field_key] = serializer_field_value or ''

            serializer_data.append(field_data)                

        return serializer_data
    
    def deserialize(self, *args, **kwargs) -> tuple[Optional[models.Model], dict]:
        """
        Десериализует входящие данные.
        """
        if self.data_type == 'rest':
            return self.deserialize_rest_data(*args, **kwargs)
        elif self.data_type == 'form':
            return self.deserialize_form_data(*args, **kwargs)

    def deserialize_rest_data(self, request_data, method: str, obj_id: Optional[int] = None):
    # def deserialize_rest_data(self, request_data, method: str = 'create', obj_id: Optional[int] = None):
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
        model_data = [request_data] if isinstance(request_data, dict) else request_data
        serializer_fields = self.get_serializer_fields()

        error_data = {}
        if obj_id:
            some_model = some_model_class.objects.get(id=obj_id)
        else:
            some_model = some_model_class()

        for field_data in model_data:
            for field_name, field_value in field_data.items():
                if field_name == 'id':
                    continue

                try:
                    serializer_field = serializer_fields.filter(name=field_name).first()
                    input_handler: FieldHandler = serializer_field.get_handler()
                    transform_field_name, transform_field_value, error = input_handler.get_transform_data(field_value, serializer_field)
                    error_data[field_name] = error
                    setattr(some_model, transform_field_name, transform_field_value)
                except Exception as error:
                    print(f'DataConnector.deserialize() error in field {field_name}', error)
                    error_data[field_name] = error

        some_model.data_connector_finish_save = True
        some_model.save()
            
        return [some_model]

    # def deserialize_form_data(self, request_data, method: str, obj_id: Optional[int] = None):
    def deserialize_form_data(self, request_data, method: str = 'create', id_field_name: str = 'id', id_field_value: Union[int, str] = None) -> tuple[Optional[models.Model], list]:
        """
        Десериализует входящие данные в формате FORM.
        """
        print(f'DataConnector.deserialize_form_data() !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(f'method: {method}')
        some_model_class: models.Model = self.content_type.model_class()
        model_data = [request_data] if isinstance(request_data, dict) else request_data
        serializer_fields = self.get_serializer_fields()
        
        error_data = {}
        some_model = None
        if method == 'get':
            if id_field_value:
                some_model = some_model_class.objects.filter(**{id_field_name: id_field_value}).first()

            if some_model:
                return some_model, model_data
            
            raise Exception(f'model: {some_model_class} with id_field_name: {id_field_name} id_field_value: {id_field_value} not found')
        
        elif method == 'create':
            some_model = some_model_class()

        elif method == 'get_or_create':     
            if id_field_value:
                some_model = some_model_class.objects.filter(**{id_field_name: id_field_value}).first()   

            if some_model:
                return some_model, model_data
            else:
                some_model = some_model_class()         
                           
        elif method == 'get_and_update_or_create':
            if id_field_value:
                some_model = some_model_class.objects.filter(**{id_field_name: id_field_value}).first()   

            if not some_model:
                some_model = some_model_class()     
        
        # Десериализация данных
        many_to_many_fields = []
        for model_field_data in model_data:
            if model_field_data.get('type') in ['ManyToManyField', 'PseudoManyToManyField', 'GenericRelation']:
                many_to_many_fields.append(model_field_data)
                continue

            field_name = model_field_data.get('name')
            print(f'field_name: {field_name} =======================================================')
            field_value = model_field_data.get('value')

            serializer_field = serializer_fields.filter(name=field_name).first()

            input_handler: IncomingFieldHandler = serializer_field.get_input_handler()
            transform_field_name, transform_field_value, error = input_handler.get_transform_data(field_value, serializer_field)

            print(f'transform_field_name: {transform_field_name}')
            # print(f'transform_field_value: {transform_field_value}')

            setattr(some_model, transform_field_name, transform_field_value)

        some_model.save()

        for many_to_many_field in many_to_many_fields:
            field_name = many_to_many_field.get('name')
            field_value = many_to_many_field.get('value')

            serializer_field = serializer_fields.filter(name=field_name).first()
            input_handler: IncomingFieldHandler = serializer_field.get_input_handler()
            input_handler.some_model = some_model
            transform_field_name, transform_field_value, error = input_handler.get_transform_data(field_value, serializer_field)
            # error_data[field_name] = error            
            # setattr(some_model, transform_field_name, transform_field_value)
        
        some_model.data_connector_finish_save = True
        some_model.save()

        return some_model, model_data

    def get_serializer_fields_class(self):
        """
        Возвращает класс полей сериализатора.
        """
        return self.serializer_fields.model

    def get_serializer_fields(self, filter={'is_active': True}):
        """
        Получает поля сериализатора.
        
        Returns:
            QuerySet: Набор полей сериализатора.
        """
        try:
            serializer_fields = self.serializer_fields.filter(**filter).order_by('order')
            return serializer_fields
        except Exception as error:
            print('DataConnector not serializer_fields')
            # print('DataConnectorMixin.get_serializer_fields() error', error)
            # traceback.print_exc()
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

