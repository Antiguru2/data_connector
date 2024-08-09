from pprint import pprint
from rest_framework import serializers

from django.contrib.contenttypes.models import ContentType

from html_constructor.models import (
    HTMLConstruktor,
)


class HTMLConstruktorSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = HTMLConstruktor
        fields = [
            'id', 
            'content_type', 
            'object_id', 
            'related_object'
        ]


