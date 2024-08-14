from pprint import pprint
from rest_framework import serializers

from django.contrib.contenttypes.models import ContentType

from html_constructor.models import (
    BaseHTMLBlock,
)


class DefaultSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        fields = '__all__'


class BaseHTMLBlockSerializer(DefaultSerializer):
    
    def get_template_body(self, instance):
        return instance.get_template_body()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['template_body'] = self.get_template_body(instance)
        return data
    
    class Meta(DefaultSerializer.Meta):
        model = BaseHTMLBlock
        fields = [
            'id',
            'name',
        ]


SERIALIZER_CLASSES = DefaultSerializer.__subclasses__()

def get_serializer_class_by_lower_name(lower_name) -> serializers.HyperlinkedModelSerializer:
    """
        Возвращает класс сериализатора по названию
    """
    for some_serializer_class in SERIALIZER_CLASSES:
        if some_serializer_class.__name__.lower() == lower_name:
            return some_serializer_class
