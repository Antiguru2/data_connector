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
    if created:
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
            try:
                if field_type == 'AutoField':
                    field_type = 'default'
                handler, created = FieldHandler.objects.get_or_create(
                    name=field_type,
                    slug=field_type,
                )
            except:
                handler = None           

            # print('dir(model_field)', dir(model_field))

            serializer_field = SerializerField.objects.create(
                data_connector=instance,
                name=verbose_name,
                slug=model_field.name,
                handler=handler,
                type=field_type,
            )
            
