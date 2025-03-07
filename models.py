import requests

from typing import Optional

from django.db import models
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .submodules.base_content_objects import BaseContentObject, SlugNamedAbstractModel


class FieldHandler(SlugNamedAbstractModel):
    """
        Класс, инструкция для обработки поля.
    """

    method = models.CharField(
        max_length=255,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = 'Обработчик поля'
        verbose_name_plural = 'Обработчики полей'

    @classmethod
    def get_default_handler(cls):
        default_handler, created = cls.objects.get_or_create(slug='default')
        return default_handler

    def get_value(self, obj, serializer_field: models.Model):
        # print('get_value============================')
        # print('slug', serializer_field.slug)
        # print('self.slug', self.slug)
        # print('obj', obj)
        serializer_field_slug = serializer_field.slug
        value = 'Не найдено'
        if hasattr(obj, serializer_field_slug):
            try:
                value = getattr(obj, serializer_field_slug)
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'

        if self.slug == 'default':
            if hasattr(obj, serializer_field_slug):
                try:
                    value = getattr(obj, serializer_field_slug)
                except Exception as e:
                    print(e)
                    value = f'Ошибка: {e}'

        elif self.slug == 'serializer':
            print('self.slug', self.slug)
            print('serializer_field_slug', serializer_field_slug)
            serializer: DataConnector = serializer_field.serializer
            print('serializer', serializer)
            if not serializer:
                value = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                if serializer_field.type == 'ForeignKey':
                    # queryset = getattr(obj, serializer_field_slug).all()
                    queryset = [getattr(obj, serializer_field_slug)]
                elif serializer_field.type == 'OneToOneField':
                    queryset = [getattr(obj, serializer_field_slug)]
                elif serializer_field.type == 'ManyToManyField':
                    queryset = getattr(obj, serializer_field_slug).all()
                elif serializer_field.type == 'GenericForeignKey':
                    related_class = serializer.content_type.model_class()
                    queryset = related_class.objects.filter(
                        content_type=ContentType.objects.get_for_model(obj),
                        object_id=obj.id,
                    )                   

                # print('queryset', queryset)
                if not queryset or queryset == [None]:
                    value = None
                else:
                    value = serializer.get_data(queryset)
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'

        elif self.slug == 'ForeignKey':
            # print('ForeignKey')
            # print('self.slug', self.slug)
            try:
                rel_object = getattr(obj, serializer_field_slug)
                if rel_object:
                    value = rel_object.id
                else:
                    value = None
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'    

        elif self.slug == 'OneToOneField':
            try:
                object = getattr(obj, serializer_field_slug)
                value = object.id
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'  

        elif self.slug == 'ManyToManyField':
            try:
                value = getattr(obj, serializer_field_slug).all().values_list('id', flat=True)
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}' 

        elif self.slug == 'FileField':
            try:
                file = getattr(obj, serializer_field_slug)
                if not file:
                    value = None
                else:
                    value = file.url
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'           

        # print('value', value)   
        return value
    
    def get_transform_data(self, value, serializer_field: models.Model) -> type:
        print('get_transform_data')
        field_error_data = {}
        transform_field_name = serializer_field.slug
        transform_field_value = value

        if self.slug == 'ForeignKey':
            try:
                if value is dict:
                    field_error_data[serializer_field.slug] = 'Обработчик ожидает идентификатор обьекта, но получил dict'

                else:
                    if 'id' not in serializer_field.slug:
                        transform_field_name += '_id'
                        # transform_field_value = int
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'  
                field_error_data[serializer_field.slug] = f'Ошибка: {e}'

        elif self.slug == 'serializer':
            serializer: DataConnector = serializer_field.serializer
            print('serializer', serializer)
            print('transform_field_value', transform_field_value)
            if not serializer:
                field_error_data[serializer_field.slug] = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                if serializer_field.type == 'ForeignKey':
                    transform_field_value = serializer.deserialize(transform_field_value, method='POST').first()
                elif serializer_field.type == 'OneToOneField':
                    pass
                elif serializer_field.type == 'ManyToManyField':
                    pass
                elif serializer_field.type == 'GenericForeignKey':
                    pass                 
            except Exception as e:
                print(e)
                field_error_data[serializer_field.slug] = f'Ошибка: {e}'

        print('transform_field_value', transform_field_value)   
        return transform_field_name, transform_field_value, field_error_data
    

class IncomingFieldHandler(SlugNamedAbstractModel):
    """
        Класс, инструкция для обработки поля.
    """

    method = models.CharField(
        max_length=255,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = 'Обработчик входящих данных'
        verbose_name_plural = 'Обработчики входящих данных'

    @classmethod
    def get_default_handler(cls):
        default_handler, created = cls.objects.get_or_create(slug='default')
        return default_handler

    def get_value(self, obj, serializer_field: models.Model):
        serializer_field_slug = serializer_field.slug
        value = 'Не найдено' 
        return value


class SerializerField(SlugNamedAbstractModel):
    """
        Класс, представляющий поле сериализатора.
    """
    TYPE_CHOICES = (
        ('AutoField', 'AutoField'),

        ('CharField', 'CharField'),
        ('TextField', 'TextField'),
        ('SlugField', 'SlugField'),
        ('EmailField', 'EmailField'),

        ('IntegerField', 'IntegerField'),
        ('PositiveIntegerField', 'PositiveIntegerField'),
        ('FloatField', 'FloatField'),
        # ('DecimalField', 'DecimalField'),
        
        ('BooleanField', 'BooleanField'),

        ('DateField', 'DateField'),
        ('TimeField', 'TimeField'),
        ('DateTimeField', 'DateTimeField'),

        ('SlugField', 'SlugField'),
        ('URLField', 'URLField'),
        ('JSONField', 'JSONField'),

        ('FileField', 'FileField'),
        
        ('ForeignKey', 'ForeignKey'),
        ('ManyToManyField', 'ManyToManyField'),
        ('OneToOneField', 'OneToOneField'),
        ('GenericRelation', 'GenericRelation'),
        ('GenericForeignKey', 'GenericForeignKey'),
    )
    slug = models.SlugField(
        max_length=255,
        unique=False,
    )
    handler = models.ForeignKey(
        FieldHandler, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name=FieldHandler._meta.verbose_name,
    )
    incoming_handler = models.ForeignKey(
        IncomingFieldHandler, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name=IncomingFieldHandler._meta.verbose_name,
    )
    data_connector = models.ForeignKey(
        'DataConnector', 
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name='Сериализатор',
        related_name='serializer_fields',
    )
    alt_key = models.CharField(
        max_length=255,
        null=True, blank=True,
        verbose_name='Альтернативный ключ',
        help_text='С таким ключем будут возвращены данные.'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
    )
    type = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES,
        default='AutoField',
        verbose_name='Тип',
    )
    serializer = models.ForeignKey(
        'DataConnector', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name='Сериализатор',
    )

    class Meta:
        verbose_name = 'Поле сериализатора'
        verbose_name_plural = 'Поля сериализатора'
    
    def __str__(self):
        result = self._meta.verbose_name
        if self.name:
            result = f"{result}: {self.name}"

        return result
    
    def get_handler(self):
        handler = self.handler

        if not handler:
            handler = FieldHandler.get_default_handler()

        return handler
    
    def get_input_handler(self):
        handler = self.handler

        if not handler:
            handler = FieldHandler.get_default_input_handler()

        return handler
    

class DataConnector(
    BaseContentObject,
):
    """
        Модель для настройки сериализации данных.
    """
    # TODO: Сейчас установлен уникальный slug, но нужно сделать, что бы слаг был уникальным только для отдельных моделей
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, blank=True,
    )

    # Разрешения
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
    )
    is_allow_view = models.BooleanField(
        default=True,
        verbose_name='Разрешить просмотр',
    )
    is_allow_edit = models.BooleanField(
        default=False,
        verbose_name='Разрешить редактирование',
    )
    is_allow_delete = models.BooleanField(
        default=False,
        verbose_name='Разрешить удаление',
    )
    is_allow_create = models.BooleanField(
        default=False,
        verbose_name='Разрешить создание',
    )


    class Meta: 
        verbose_name = 'Сериализатор'
        verbose_name_plural = 'Сериализаторы'

    # def __str__(self) -> str:
    #     result = super().__str__()
    #     if self and self._meta.verbose_name:
    #         result = self._meta.verbose_name

    #         if self.name:
    #             result += f': {self.name}'

    #     return result

    @property
    @admin.display(description='Дополнительные кнопки')
    def additional_buttons(self):
        return self.get_additional_buttons()
    
    def get_additional_buttons(self):
        additional_buttons = ''
        if self.content_type:
            model = self.content_type.model_class()
            additional_buttons += f"<a href='/data_connector/super-api/{model._meta.app_label}__{model.__name__.lower()}/'><button>К данным</button></a>"
        return mark_safe(additional_buttons)
    
    @classmethod
    def get_self_assembly(
        cls,
        data: Optional[dict] = None,
    ):
        self_assembly = None
        return self_assembly
    

    @classmethod
    def get_serializer(
        cls,
        some_model: models.Model,
        method: str = 'GET',
        serializer_name: Optional[str] = None, 
        serializer_self_assembly_data: Optional[dict] = None
    ):    
        serializer = None
        print('some_model', some_model)
        print('some_model.__class__.__name__', some_model.__class__.__name__)
        print('serializer_self_assembly_data', serializer_self_assembly_data)
        if serializer_self_assembly_data:
            serializer = cls.get_self_assembly(serializer_self_assembly_data)

        else:
            content_type = ContentType.objects.get_for_model(some_model)
            # print('content_type', content_type)
            # print('content_type.id', content_type.id)
            all_serializers = cls.objects.all()
            # print('all_serializers', all_serializers)
            # print('all_serializers ids', all_serializers.values_list('id', flat=True))
            # print('all_serializers content_types', all_serializers.values_list('content_type', flat=True))
            
            serializers = all_serializers.filter(
                content_type=content_type,
            )
            print('serializers', serializers)
            if serializer_name:
                serializers = serializers.filter(name=serializer_name)

            if serializers:
                serializer = serializers.first()

        if serializer and not serializer.is_active:
            serializer = None

        return serializer

    def set_data(self, request_data: dict, method: str, obj_id: Optional[int] = None):
        print('set_data')
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
    
    def get_data(self, queryset):
        response_data = {}
        try:
            response_data = self.serialize(queryset)
        except Exception as error:
            # print('get_data', queryset)
            print('get_data', error)

        return response_data

    def serialize(self, queryset=None):
        """
        Метод для сериализации данных модели.
        """
        serializer_data = []
        for obj in queryset:
            fields_data = {}
            serializer_fields = self.serializer_fields.filter(is_active=True).all()
            for serializer_field in serializer_fields:
                serializer_field: SerializerField
                handler: FieldHandler = serializer_field.get_handler()
                if not handler:
                    fields_data[serializer_field.slug] = 'Oбработчик не настроен'
                else:
                    serializer_field_slug = serializer_field.slug
                    if serializer_field.alt_key:
                        serializer_field_slug = serializer_field.alt_key
                        
                    fields_data[serializer_field_slug] = handler.get_value(obj, serializer_field)

            if fields_data:
                serializer_data.append(fields_data)

        return serializer_data
    
    def deserialize(self, request_data, method: str, obj_id: Optional[int] = None):
        """
        Метод для десериализации данных модели.
        """
        some_model_class = self.content_type.model_class()
        request_data_list = [request_data] if type(request_data) == dict else request_data
        serializer_fields = self.serializer_fields.filter(is_active=True).all()
        print('serializer_fields', serializer_fields.values_list('slug', flat=True))

        error_data = {}
        if obj_id:
            some_model = some_model_class.objects.get(id=obj_id)
        else:
            some_model = some_model_class()

        print('request_data_list', request_data_list)
        for request_data_dict in request_data_list:
            print('request_data_dict', request_data_dict)
            for field_name, field_value in request_data_dict.items():
                if field_name == 'id':
                    continue

                print('field_name', field_name)
                print('field_value', field_value)
                try:
                    serializer_field = serializer_fields.filter(slug=field_name).first()
                    input_handler: FieldHandler = serializer_field.get_handler()
                    transform_field_name, transform_field_value, error = input_handler.get_transform_data(field_value, serializer_field)
                    setattr(some_model, transform_field_name, transform_field_value)
                except Exception as error:
                    print(f'DataConnector.deserialize() error in field {field_name}', error)

                finally:
                    error_data[field_name] = error

                some_model.save()
                queryset = some_model_class.objects.filter(id=some_model.id)

        print('error_data', error_data)
        return queryset


class RemoteSite(models.Model):
    """
        Модель для хранения информации о удалённых сайтах.
    """
    main = models.BooleanField(default=False, editable=False)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)

    class Meta: 
        verbose_name = 'Удалённый сайт'
        verbose_name_plural = 'Удалённые сайты'

    def __str__(self) -> str:
        result = super().__str__()
        if self._meta.verbose_name:
            result = self._meta.verbose_name

            if self.name:
                result += f': {self.name}'

        return result
    

class Transmitter(models.Model):
    """
        Модель для передачи данных моделей через админку.
    """
    ACTIONS_CHOICES = (
        ('send', 'Передать'),
        ('receive', 'Получить'),
    )
    MODES_CHOICES = (
        ('test', 'Тестирование'),
        ('ordinary', 'Обычный'),
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название',
    )
    action = models.CharField(
        max_length=255, 
        choices=ACTIONS_CHOICES, 
        default='receive',
        verbose_name='Действие',
    )
    mod = models.CharField(
        max_length=255, 
        choices=MODES_CHOICES, 
        default='ordinary',
        verbose_name='Режим',
    )
    serializer = models.ForeignKey(
        DataConnector, 
        blank=True, null=True,
        on_delete=models.CASCADE, 
        verbose_name=DataConnector._meta.verbose_name,
    )
    model_id = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name="ID модели",
    )
    filter = models.JSONField(
        default=dict, blank=True,
        verbose_name="Фильтр(kwargs)",
    )
    remote_site = models.ForeignKey(
        RemoteSite, 
        blank=True, null=True,
        on_delete=models.SET_NULL,   
        verbose_name=RemoteSite._meta.verbose_name,
    )
    run_on_save = models.BooleanField(
        default=False,
        verbose_name='Запустить при сохранении',
    )


    class Meta: 
        verbose_name = 'Передатчик'
        verbose_name_plural = 'Передатчики'

    def __str__(self) -> str:
        result = super().__str__()
        if self._meta.verbose_name:
            result = self._meta.verbose_name

            if self.name:
                result += f': {self.name}'

        return result

    def start(self):
        print('start')
        execute = True
        if not self.remote_site:
            execute = False
            TransmitterLog.objects.create(
                transmitter=self,
                status='failure',
                error='Сайт назначения не указан',
            )

        if not self.serializer:
            execute = False
            TransmitterLog.objects.create(
                transmitter=self,
                status='failure',
                error='Сериализатор не указан',
            )

        if execute:
            SomeModel: models.Model = self.serializer.content_type.model_class()
            if self.model_id:
                queryset = SomeModel.objects.filter(id=self.model_id)

            elif self.filter:
                queryset = SomeModel.objects.filter(**self.filter)

            else:
                queryset = SomeModel.objects.all()

            if self.action == 'send':
                serializer_data = self.serializer.serialize(queryset)
                heders = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Token e37c658100769f79b4f9cc347265060651b3a9e6'
                }
                print('serializer_data', serializer_data)
                print('heders', heders)
                response = requests.post(
                    f'https://{self.remote_site.domain}/data_connector/super-api/{self.serializer.content_type.app_label}__{self.serializer.content_type.model}/',
                    headers=heders,
                    json={'data': serializer_data},   
                )
                if response.status_code != 200:
                    TransmitterLog.objects.create(
                        transmitter=self,
                        status='failure',
                        result=response.text,
                    )
                else:
                    TransmitterLog.objects.create(
                        transmitter=self,
                        status='success',
                        result=response.text,
                    )


        if self.run_on_save:
            self.run_on_save = False
            self.save()


class TransmitterLog(models.Model):
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('pending', 'В ожидании'),
        ('success', 'Успешно'),
        ('failure', 'Ошибка'),
    )

    transmitter = models.ForeignKey(
        Transmitter, 
        on_delete=models.CASCADE, 
        verbose_name='Трансмиттер'
    )
    status = models.CharField(
        max_length=255, 
        choices=STATUS_CHOICES, 
        default='new'
    )
    date = models.DateTimeField(auto_now_add=True)
    result = models.JSONField(
        blank=True, null=True,
        verbose_name="Результат",
    )

    class Meta: 
        verbose_name = 'Лог передачи'
        verbose_name_plural = 'Логи передач'

    def __str__(self) -> str:
        result = super().__str__()
        if self._meta.verbose_name:
            result = self._meta.verbose_name

            if self.status:
                result += f': {self.status}'

        return result