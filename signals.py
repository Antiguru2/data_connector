import os
import json

from django.conf import settings
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import (
    pre_delete, 
    pre_save,
    post_save,
    post_delete,
    post_migrate,
)
# from django.db.utils import OperationalError

from .models import (
    RemoteSite,
    Transmitter,
    DataConnector,
    SerializerField,
    FieldHandler,
    FormFieldHandler
)

try:
    from .local_settings import MAIN_SITE_DOMAIN
except:
    MAIN_SITE_DOMAIN = ''


main_site_dict = {
    'main': True,
    'name': 'base_store',
    'domain': 'basestore.online',
}

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'data_connector':
        main_site, created = RemoteSite.objects.get_or_create(**main_site_dict)
        if created:
            ...
            # TODO Нужно сделать запрос на base_store, и получить остальные сайты и отправить этот туда
        # serializer__content_type = ContentType.objects.get_for_model(ContentType)

        # print('Обновление базового сериализатора для контент типов')
        # base_serializer_content_type = DataConnector.objects.filter(
        #     content_type=serializer__content_type,
        # ).first()
        # if not base_serializer_content_type:
        #     base_serializer_content_type = DataConnector.objects.create(
        #         name='Базовый сериализатор для контент типов',
        #         slug='base_serializer_content_type',
        #         content_type=serializer__content_type,
        #         description=str(
        #             'Базовый сериализатор для контент типов предназначен для самосериализации контент типов'
        #             'Он создаётся и восстанавливается автоматически при миграции'
        #         ),
        #     )

        # update_base_serializer_fields(base_serializer_content_type, os.path.join(settings.BASE_DIR, 'data_connector/fixtures/base_serializer_content_type__fields_dump.json'))

        # content_type__serializer = ContentType.objects.get_for_model(DataConnector)    

        # print('Обновление базового сериализатора')
        # base_serializer = DataConnector.objects.filter(
        #     content_type=content_type__serializer,
        # ).first()
        # if not base_serializer:
        #     base_serializer = DataConnector.objects.create(
        #         name='Базовый сериализатор',
        #         slug='base_serializer',
        #         content_type=content_type__serializer,
        #         description=str(
        #             'Базовый сериализатор предназначен для самосериализации модели DataConnector'
        #             'Он создаётся и восстанавливается автоматически при миграции'
        #         ),
        #     )

        # update_base_serializer_fields(base_serializer, os.path.join(settings.BASE_DIR, 'data_connector/fixtures/base_serializer__fields_dump.json'))

        # print('Обновление базового сериализатора для полей')
        # content_type__serializer_field = ContentType.objects.get_for_model(SerializerField)
        # base_serializer_for_fields = DataConnector.objects.filter(
        #     content_type=content_type__serializer_field,
        # ).first()
        # if not base_serializer_for_fields:
        #     base_serializer_for_fields = DataConnector.objects.create(
        #         name='Базовый сериализатор для полей',
        #         slug='base_serializer_for_fields',
        #         content_type=content_type__serializer_field,
        #         description=str(
        #             'Базовый сериализатор для полей предназначен для самосериализации полей модели DataConnector'
        #             'Он создаётся и восстанавливается автоматически при миграции'
        #         ),
        #     )

        # update_base_serializer_fields(base_serializer_for_fields, os.path.join(settings.BASE_DIR, 'data_connector/fixtures/base_serializer_fields__fields_dump.json'))

        # serializer_fields_field = base_serializer.serializer_fields.filter(name='serializer_fields').first()
        # serializer_fields_field.serializer = base_serializer_for_fields
        # serializer_fields_field.data_type = 'form'
        # serializer_fields_field.save()

        # serializer_fields_content_type = base_serializer.serializer_fields.filter(name='content_type').first()
        # serializer_fields_content_type.serializer = base_serializer_content_type
        # serializer_fields_content_type.data_type = 'rest'
        # serializer_fields_content_type.save()

        # serializer_fields_serializer = base_serializer_for_fields.serializer_fields.filter(name='serializer').first()
        # serializer_fields_serializer.serializer = base_serializer
        # serializer_fields_serializer.data_type = 'form'
        # serializer_fields_serializer.save()


def update_base_serializer_fields(serializer: DataConnector, dump_path: str):
    with open(dump_path, 'r') as f:
        serializer_fields_dump: list[dict] = json.load(f)

    for serializer_field_dump in serializer_fields_dump:
        serializer_field, created = SerializerField.objects.get_or_create(
            name=serializer_field_dump['name'],
            data_connector=serializer,
        )
        for field_name, field_value in serializer_field_dump.items():
            if field_name == 'name':
                continue

            # if field_name == 'serializer_fields':
            setattr(serializer_field, field_name, field_value)
        serializer_field.save()


@receiver(post_save, sender=Transmitter)
def update_statistic(sender, instance, **kwargs):
    if instance.run_on_save:
        instance.start()


    # old_instance = Transmitter.objects.get(id=instance.id)


@receiver(post_save, sender=DataConnector)
def create_serializer_fields(sender: DataConnector, instance: DataConnector, created: bool, **kwargs):
    '''
    В сигнале создаются поля сериализатора которые представляют из себя поля модели к которой привязан DataConnector
    '''
    if created and instance.content_type:
        if hasattr(instance, 'data_connector_finish_save'):
            return

        model_fields = instance.content_type.model_class()._meta.get_fields()
        for model_field in model_fields:
            
            # print('model_field', model_field)
            # print('model_field.name', model_field.name)
            try:
                verbose_name = model_field.verbose_name
            except:
                verbose_name = model_field.name

            try:
                field_type = model_field.get_internal_type()
            except AttributeError:
                if model_field.name == 'related_object':
                    field_type = 'GenericRelation'

            related_model = None
            serializer_field_name = model_field.name

            # print('field_type', field_type)
            # print('serializer_field_name', serializer_field_name)

            if field_type in ('ManyToOneRel', 'GenericRelation'):
                if hasattr(model_field, 'related_name') and model_field.related_name:
                    serializer_field_name = model_field.related_name
                else:
                    serializer_field_name = f'{model_field.name}_set'

                # Для структуы
                if hasattr(model_field, 'related_model') and model_field.related_model:
                    related_model = model_field.related_model


            # print('related_model', related_model)
            serializer_field = instance.get_serializer_fields_class().objects.create(
                data_connector=instance,
                verbose_name=verbose_name,
                name=serializer_field_name,
                type=field_type,
            )
            
