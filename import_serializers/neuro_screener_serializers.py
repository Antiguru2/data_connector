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
    name = serializers.CharField(source='candidat_full_name')
    experience = serializers.CharField(source='experience_text')
    ai_comment = serializers.CharField(source='comment')
    resume_url = serializers.CharField(source='hh_url')
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
            'name',
            'resume_url',
            'category',
            'ai_comment',
            'comment',
            'experience',
            'is_viewed',
            'is_analyzed',
            'is_analyzing',
            'questions',
            'google_docs_file_id',
            'answers',
            'username',
            'interview_date',
            'salary',
            'age',
            'gender',
            'area',
            'contact_email',
            'contact_phone',
            'total_experience_years',
            'experience_json',
            'job_search_status',
        ]

    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"UPDATE CANDIDATE DATA: {validated_data}")
        
        if 'comment' in self.initial_data:
            logger.info(f"DIRECT COMMENT UPDATE: {self.initial_data['comment']}")
            instance.comment = self.initial_data['comment']
        
        if 'comment' in validated_data:
            logger.info(f"COMMENT from validated_data: {validated_data['comment']}")
            instance.comment = validated_data['comment']
            
        return super().update(instance, validated_data)


# class ProjectImportSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = [
#             'id',
#             'status',
#             'description',
#             'json_prompts',
#         ]