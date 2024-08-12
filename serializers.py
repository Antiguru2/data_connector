from pprint import pprint
from rest_framework import serializers

from django.contrib.contenttypes.models import ContentType

from html_constructor.models import (
    BaseHTMLBlock,
)


class DefaultSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        fields = '__all__'


class BaseHTMLBlockSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = BaseHTMLBlock
        fields = [
            'id',
            'name',
        ]

