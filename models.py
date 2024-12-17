from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .submodules.super_object import AbstractRelatedObject
from .submodules.base_content_objects import BaseContentObject


class SerializerField(models.Model):
    """
        Класс, представляющий поле сериализатора с полями name и method.
    """
    name = models.CharField(max_length=255)
    method = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Поле сериализатора'
        verbose_name_plural = 'Поля сериализатора'
    
    def __str__(self):
        result = self._meta.verbose_name
        if self.name:
            result = f"{result}: {self.name}"

        return result
    

class DataConnector(
    AbstractRelatedObject, 
    BaseContentObject,
):
    """
        Модель для настройки сериализации данных.
    """
    serialized_fields = models.JSONField(
        blank=True, null=True,
        verbose_name="Поля для сериализации(словарь)",
        help_text="Если пустое, то все поля будут сериализованы"
    )
    serializer_fields = models.ManyToManyField(
        SerializerField,
        related_name='data_connectors',
        blank=True
    )

    # def serialize(self):
    #     """
    #     Метод для сериализации данных модели.
    #     """
    #     class DataConnectorSerializer(serializers.ModelSerializer):
    #         serializer_fields = serializers.SerializerMethodField()

    #         class Meta:
    #             model = self.__class__  # Используйте текущий класс как модель для сериализации
    #             fields = ['id', 'slug', 'name', 'description', 'content_type', 'object_id', 'serializer_fields']
                
    #         def get_serializer_fields(self, obj):
    #             return [{'name': field.name, 'method': field.method} for field in obj.serializer_fields.all()]
        
    #     serializer = DataConnectorSerializer(self)
    #     return serializer.data


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
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('pending', 'В ожидании'),
        ('success', 'Успешно'),
        ('failure', 'Ошибка'),
    )
    name = models.CharField(max_length=255)
    action = models.CharField(
        max_length=255, 
        choices=ACTIONS_CHOICES, 
        default='receive'
    )
    serializer = models.ForeignKey(
        DataConnectorAbstractModel, 
        on_delete=models.CASCADE, 
        verbose_name='Сериализатор'
    )
    model_id = models.PositiveIntegerField()
    filter = models.JSONField(
        blank=True, null=True,
        verbose_name="Фильтр(kwargs)",
    )
    status = models.CharField(
        max_length=255, 
        choices=STATUS_CHOICES, 
        default='new'
    )

    class Meta: 
        verbose_name = 'Трансмиттер'
        verbose_name_plural = 'Трансмиттеры'

    def __str__(self) -> str:
        result = super().__str__()
        if self._meta.verbose_name:
            result = self._meta.verbose_name

            if self.name:
                result += f': {self.name}'


class TransmitterLog(models.Model):
    transmitter = models.ForeignKey(
        Transmitter, 
        on_delete=models.CASCADE, 
        verbose_name='Трансмиттер'
    )
    status = models.CharField(
        max_length=255, 
        choices=Transmitter.STATUS_CHOICES, 
        default='new'
    )
    date = models.DateTimeField(auto_now_add=True)
    result = models.JSONField(
        blank=True, null=True,
        verbose_name="Результат",
    )