import requests
import traceback

from typing import Optional

from django.db import models
from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .submodules.base_content_objects.abstract_models import BaseContentObject
from .submodules.base_content_objects.mixins import AdminChangeButtonMixin
from data_connector.abstract_models import (
    SerializerFieldAbstractModel,
    DataConnectorAbstractModel,
)
from data_connector.mixins import (
    SerializerFieldMixin, 
    DataConnectorMixin,
)
from .field_handlers import *




class SerializerField(
    SerializerFieldMixin,
    SerializerFieldAbstractModel, 
):
    """
    Класс, представляющий поле сериализатора данных.
    
    Этот класс объединяет функциональность SerializerFieldMixin и SerializerFieldAbstractModel,
    предоставляя полный набор возможностей для работы с сериализацией полей модели.
    
    Основные возможности:
    - Наследование базовых полей и методов от SerializerFieldAbstractModel
    - Использование функциональности обработчиков из SerializerFieldMixin
    - Связь с основным сериализатором (data_connector)
    - Связь с вложенным сериализатором для обработки связанных данных
    - Поддержка различных типов обработчиков данных
    
    Атрибуты:
        data_connector (ForeignKey): Связь с основным сериализатором, определяющим
            контекст и правила обработки данных.
        serializer (ForeignKey): Связь с вложенным сериализатором для обработки
            связанных данных и вложенных объектов.
    
    Пример использования:
        ```python
        # Создание поля для сериализации
        field = SerializerField(
            name='Название поля',
            verbose_name='field_name',
            type='CharField',
            data_connector=main_serializer,
            serializer=nested_serializer  # опционально
        )
        ```
        
    Примечания:
        - Поле data_connector является обязательным для корректной работы
        - Поле serializer используется только для обработки связанных данных
        - Все базовые поля (verbose_name, type, is_active и т.д.) наследуются от
          SerializerFieldAbstractModel
        - Все методы обработки данных наследуются от SerializerFieldMixin
    """
    data_connector = models.ForeignKey(
        'DataConnector', 
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('Сериализатор'),
        related_name='serializer_fields',
        help_text=_('Сериализатор, к которому относится это поле. '
                   'Определяет контекст и правила обработки данных.'),
    )
    serializer = models.ForeignKey(
        'DataConnector', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name=_('Вложенный сериализатор'),
        related_name='parent_serializer_fields',
        help_text=_('Сериализатор для обработки связанных данных. '
                   'Используется для вложенных объектов и связей.'),
    )

    class Meta:
        verbose_name = _('Поле сериализатора')
        verbose_name_plural = _('Поля сериализатора')
    

class DataConnector(
    DataConnectorAbstractModel, 
    DataConnectorMixin,
    AdminChangeButtonMixin,
):
    """
    Класс для настройки сериализации данных.
    
    Этот класс объединяет функциональность DataConnectorAbstractModel и DataConnectorMixin,
    предоставляя полный набор возможностей для работы с сериализацией данных модели.
    
    Основные возможности:
    - Наследование базовых полей и методов от DataConnectorAbstractModel
    - Использование функциональности сериализации из DataConnectorMixin
    - Управление правами доступа (просмотр, редактирование, удаление, создание)
    - Сериализация данных в различных форматах (REST, FORM)
    - Десериализация входящих данных
    - Автоматическая инициализация полей сериализатора
    
    Атрибуты:
        content_type (ForeignKey): Связь с моделью, для которой настраивается сериализация.
        is_active (BooleanField): Флаг активности сериализатора.
        is_allow_view (BooleanField): Разрешение на просмотр данных.
        is_allow_edit (BooleanField): Разрешение на редактирование данных.
        is_allow_delete (BooleanField): Разрешение на удаление данных.
        is_allow_create (BooleanField): Разрешение на создание данных.
    
    Пример использования:
        ```python
        # Получение сериализатора для модели
        serializer = DataConnector.get_serializer(
            some_model=MyModel,
            user=request.user,
            method='GET',
            data_type='rest'
        )
        
        # Сериализация данных
        data = serializer.get_data(queryset)
        ```
        
    Примечания:
        - Все базовые поля (content_type, is_active и т.д.) наследуются от
          DataConnectorAbstractModel
        - Все методы сериализации и обработки данных наследуются от
          DataConnectorMixin
        - Для корректной работы требуется указать content_type
    """
    data_type = 'form'
    
    class Meta:
        verbose_name = _('Сериализатор')
        verbose_name_plural = _('Сериализаторы')


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
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Token 1f1fee896c312a8d81b307fba57cbc6ffdc69b07'
                }
                print('serializer_data', serializer_data)
                print('headers', headers)
                response = requests.post(
                    f'https://{self.remote_site.domain}/data_connector/super-api/{self.serializer.content_type.app_label}__{self.serializer.content_type.model}/',
                    headers=headers,
                    json={'data': serializer_data},   
                    verify=False, 
                )
                print('response', response)
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


class ContentsTestModel(models.Model):
    """
    Модель для тестирования содержимого.
    """
    char_field = models.CharField(
        default='default_value',
        max_length=255,
        verbose_name='Название',
    )
    integer_field = models.IntegerField(
        default=0,
        verbose_name='Целое число',
    )
    float_field = models.FloatField(
        default=0.0,
        verbose_name='Число с плавающей точкой',
    )
    boolean_field = models.BooleanField(
        default=False,
        verbose_name='Булево значение',
    )
    datetime_field = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата и время',
    )
    text_field = models.TextField(
        default='default_value',
        verbose_name='Текст',
    )

    class Meta:
        abstract = True


class MainTestModel(ContentsTestModel):
    """
    Основная тестовая модель для тестирования API.
    """
    one_to_one_model = models.OneToOneField(
        'OneToOneModel',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='main_models',
    )
    for_in_key_model = models.ForeignKey(
        'ForInKeyModel',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='main_models',
    )
    many_to_many_models = models.ManyToManyField(
        'ManyToManyModel', blank=True,
        related_name='main_models',
    )


class OneToOneModel(ContentsTestModel):
    """
    Модель для тестирования OneToOne связей.
    """
    ...


class ForInKeyModel(ContentsTestModel):
    """
    Модель для тестирования ForeignKey связей.
    """

    class Meta:
        verbose_name = 'Модель с внешним ключом'
        verbose_name_plural = 'Модели с внешними ключами'


class ManyToManyModel(ContentsTestModel):
    """
    Модель для тестирования ManyToMany связей.
    """

    class Meta:
        verbose_name = 'Модель с множественной связью'
        verbose_name_plural = 'Модели с множественными связями'


class GenericRelatedModel(models.Model):
    """
    Модель для тестирования Generic Relations.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Тип контента',
    )
    object_id = models.PositiveIntegerField(
        verbose_name='ID объекта',
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id',
    )

    class Meta:
        verbose_name = 'Модель с общей связью'
        verbose_name_plural = 'Модели с общими связями'