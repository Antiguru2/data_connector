import base64
import tempfile

from rest_framework import serializers

from django.apps import apps
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile

from talent_finder.models import Project, Candidate


class CandidateImportSerializer(serializers.ModelSerializer): 
    title = serializers.CharField(source='resume_title')
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
    ) 


    class Meta:
        model = Candidate
        fields = [
            'id',
            'project',
            'hh_resume_id',
            'title',
            'hh_url',
            'category',
            'comment',
            'is_viewed',

            'questions',
            'google_docs_file_id',
            'answers',
            'username',
            'interview_date',
            'salary',
        ]


# class ProjectImportSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = [
#             'id',
#             'status',
#             'description',
#             'json_prompts',
#         ]