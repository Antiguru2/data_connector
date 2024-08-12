from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ModelConnector(models.Model):
    # input_model_name = models.CharField(
    #     max_length=255,
    #     verbose_name='Название исходной модели'
    # )
    # output_model = models.CharField(
    #     max_length=255,
    #     verbose_name='Название принимающей модели модели'
    # )

    def __str__(self):
        return self._meta.verbose_name
    
    class Meta:
        verbose_name = 'Коннектор моделей'
        verbose_name_plural = 'Коннекторы моделей'

    def get_instruction(self):
        return None