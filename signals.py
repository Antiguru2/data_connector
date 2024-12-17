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

from .models import RemoteSite


main_site_dict = {
    'main': True,
    'name': 'base_store',
    'domain': 'basestore.site',
}

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'data_connector':
        main_site = RemoteSite.objects.get_or_create(**main_site_dict)
