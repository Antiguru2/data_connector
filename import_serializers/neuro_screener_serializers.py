import base64
import tempfile

from rest_framework import serializers

from django.apps import apps
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile

from talent_finder.models import Project, Candidate
from talent_finder.management.commands.check_candidates import increment_resume_limit_usage


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
        
        # Проверяем, был ли кандидат проанализирован до обновления
        was_analyzed = instance.is_analyzed
        
        if 'comment' in self.initial_data:
            logger.info(f"DIRECT COMMENT UPDATE: {self.initial_data['comment']}")
            instance.comment = self.initial_data['comment']
        
        if 'comment' in validated_data:
            logger.info(f"COMMENT from validated_data: {validated_data['comment']}")
            instance.comment = validated_data['comment']
        
        # Обновляем кандидата
        updated_instance = super().update(instance, validated_data)
        
        # Проверяем, стал ли кандидат проанализированным после обновления
        if not was_analyzed and updated_instance.is_analyzed:
            logger.info(f"Кандидат {instance.id} был проанализирован, обновляем счетчик использования")
            
            # Получаем ID пользователя, создавшего проект
            user_id = instance.project.created_by_id
            
            # Обновляем счетчик использования лимита
            increment_result = increment_resume_limit_usage(user_id)
            logger.info(f"Результат обновления счетчика: {increment_result}")
            
        return updated_instance


# class ProjectImportSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = [
#             'id',
#             'status',
#             'description',
#             'json_prompts',
#         ]