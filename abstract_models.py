from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .submodules.base_content_objects.abstract_models import (
    NameAbstractModel as DCNameAbstractModel,
    BaseContentObject as DCBaseContentObject,
)


class SerializerFieldAbstractModel(DCNameAbstractModel):
    """
    Абстрактный класс для полей сериализатора.
    
    Этот класс предоставляет базовую структуру для создания полей сериализатора.
    Он определяет общие поля, необходимые для работы с различными типами данных
    в системе сериализации.
    
    Основные возможности:
    - Определение типа поля и его обработчиков
    - Настройка альтернативных ключей для сериализации
    - Управление активностью поля
    - Поддержка различных форматов данных (REST, FORM)
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
        ('DecimalField', 'DecimalField'),
        
        ('BooleanField', 'BooleanField'),

        ('DateField', 'DateField'),
        ('TimeField', 'TimeField'),
        ('DateTimeField', 'DateTimeField'),

        ('SlugField', 'SlugField'),
        ('URLField', 'URLField'),
        ('JSONField', 'JSONField'),

        ('FileField', 'FileField'),
        # related
        ('ForeignKey', 'ForeignKey'),
        ('ManyToManyField', 'ManyToManyField'),
        ('ManyToOneRel', 'ManyToOneRel'),
        ('OneToOneField', 'OneToOneField'),
        ('GenericRelation', 'GenericRelation'),
        ('GenericForeignKey', 'GenericForeignKey'),
        ('serializer', 'serializer'),
        # unique
        ('cargo_calc__route', 'cargo_calc__route'),
        ('cargo_calc__services', 'cargo_calc__services'),
        ('cargo_calc__prices', 'cargo_calc__prices'),
    )

    verbose_name = models.CharField(
        max_length=255,
        verbose_name=_('Человекочитаемое название'),
        # help_text=_('Человекочитаемое название поля, отображаемое в интерфейсе.'),
    )
    type_for_handler = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Тип для обработчика'),
        # help_text=_('Тип поля, используемый для обработки данных при сериализации. '
        #            'Если не указан, будет использован основной тип поля.'),
    )
    type_for_form_handler = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Тип для обработчика формы'),
        # help_text=_('Тип поля, используемый при работе с формами. '
        #            'Определяет, как поле будет отображаться и обрабатываться в формах.'),
    )
    incoming_handler = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Тип для обработчика входящих данных'),
        # help_text=_('Тип поля, используемый для обработки входящих данных. '
        #            'Определяет, как будут обрабатываться данные при десериализации.'),
    )
    alt_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Альтернативный ключ'),
        # help_text=_('Альтернативное имя поля, которое будет использоваться при сериализации. '
        #            'Позволяет изменить имя поля в выходных данных без изменения структуры модели.'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        # help_text=_('Определяет, будет ли поле участвовать в сериализации. '
        #            'Неактивные поля игнорируются при обработке данных.'),
    )
    type = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES,
        default='AutoField',
        verbose_name=_('Тип'),
        # help_text=_('Основной тип поля, определяющий его поведение и формат данных. '
        #            'Используется по умолчанию, если не указаны специальные обработчики.'),
    )

    class Meta:
        abstract = True
        verbose_name = _('Поле сериализатора')
        verbose_name_plural = _('Поля сериализатора')

    def __str__(self):
        result = super().__str__()

        try:
            if self.type:
                result += f'({self.type})'
        except:
            pass

        return result


class DataConnectorAbstractModel(DCBaseContentObject):
    """
    Абстрактный класс для сериализатора данных.
    
    Этот класс предоставляет базовую структуру для создания сериализаторов данных.
    Он определяет общие поля и методы, необходимые для работы с различными моделями
    в системе сериализации.
    
    Основные возможности:
    - Связь с конкретной моделью через ContentType
    - Управление правами доступа (просмотр, редактирование, удаление, создание)
    - Сериализация данных в различных форматах (REST, FORM)
    - Десериализация входящих данных
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Тип контента'),
        # help_text=_('Модель, которую будет обрабатывать сериализатор.'),
    )

    # Разрешения
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        # help_text=_('Определяет, будет ли сериализатор доступен для использования. '
        #            'Неактивные сериализаторы игнорируются при обработке данных.'),
    )
    is_allow_view = models.BooleanField(
        default=True,
        verbose_name=_('Разрешить просмотр'),
        # help_text=_('Разрешает просмотр данных через API.'),
    )
    is_allow_edit = models.BooleanField(
        default=False,
        verbose_name=_('Разрешить редактирование'),
        # help_text=_('Разрешает редактирование данных через API.'),
    )
    is_allow_delete = models.BooleanField(
        default=False,
        verbose_name=_('Разрешить удаление'),
        # help_text=_('Разрешает удаление данных через API.'),
    )
    is_allow_create = models.BooleanField(
        default=False,
        verbose_name=_('Разрешить создание'),
        # help_text=_('Разрешает создание новых записей через API.'),
    )

    class Meta:
        abstract = True
        verbose_name = _('Сериализатор')
        verbose_name_plural = _('Сериализаторы')

