# import os

# from django.conf import settings
from django.dispatch import receiver
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

        # form_field_handlers = FormFieldHandler.objects.all()
        # if form_field_handlers.count() < len(SerializerField.TYPE_CHOICES):
        #     for type_name, type_slug in SerializerField.TYPE_CHOICES:
        #         form_field_handler, created_ = FormFieldHandler.objects.get_or_create(
        #             # name=type_name,
        #             slug=type_slug,
        #         )

        # DataConnector.objects.get_or_create(
        #     name='Сериализатор',
        #     slug='serializer',
        # )


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
        model_fields = instance.content_type.model_class()._meta.get_fields()
        for model_field in model_fields:
            
            print('model_field', model_field)
            print('model_field.name', model_field.name)
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

            print('field_type', field_type)
            print('serializer_field_name', serializer_field_name)

            if field_type in ('ManyToOneRel', 'GenericRelation'):
                if hasattr(model_field, 'related_name') and model_field.related_name:
                    serializer_field_name = model_field.related_name
                else:
                    serializer_field_name = f'{model_field.name}_set'

                # Для структуы
                if hasattr(model_field, 'related_model') and model_field.related_model:
                    related_model = model_field.related_model


            print('related_model', related_model)
            serializer_field = instance.get_serializer_fields_class().objects.create(
                data_connector=instance,
                verbose_name=verbose_name,
                name=serializer_field_name,
                type=field_type,
            )
            
