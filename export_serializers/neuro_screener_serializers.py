import base64
import tempfile

from rest_framework import serializers

from django.apps import apps
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import get_user_model

from talent_finder.models import (
    Project, 
    Candidate, 
    SearchRow,
    SearchCriteria,
    AnalysisStatistics,
    Prompt,
    ProjectMetaData,
    HHArea,
)

User = get_user_model()


class SearchRowSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=False,
    )  
    logic = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    period = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    field = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = SearchRow
        fields = [
            'id', 

            'text', 
            'logic', 
            'period', 
            'field',

            'project',
        ]

class SearchCriteriaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=False,
    )   
    must_have = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    nice_to_have = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = SearchCriteria
        fields = [
            'id', 
            'must_have', 
            'nice_to_have',
            'additional',  
            'areas',
            'project',
        ]


class ProjectExportSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )    
    created_at = serializers.DateTimeField(read_only=True)
    last_modified = serializers.DateTimeField(read_only=True)
    
    search_rows = SearchRowSerializer(many=True)
    search_criteria = SearchCriteriaSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'status',
            'name',
            'created_by',
            'created_at',
            'last_modified',
            'description',

            'search_rows',
            'search_criteria',
            'json_prompts',
        ]

    def create(self, validated_data):
        search_rows_data = validated_data.pop('search_rows')
        search_criteria_data = validated_data.pop('search_criteria')
        project = super().create(validated_data)

        for search_row_data in search_rows_data:
            search_row_data['project'] = project.id
            search_row_serializer = SearchRowSerializer(data=search_row_data)
            if search_row_serializer.is_valid():
                search_row_serializer.save()

        for search_criterion_data in search_criteria_data:
            search_criterion_data['project'] = project.id
            search_criterion_serializer = SearchCriteriaSerializer(data=search_criterion_data)
            if search_criterion_serializer.is_valid():
                search_criteria = search_criterion_serializer.save()

        return project
    
    def update(self, instance, validated_data):
        search_rows_data = validated_data.pop('search_rows', [])
        search_criteria_data = validated_data.pop('search_criteria', [])
        
        project = super().update(instance, validated_data)

        # Получаем ID всех строк поиска, которые пришли в запросе
        incoming_search_row_ids = [row.get('id') for row in search_rows_data if row.get('id')]
        
        # Удаляем все строки поиска, которых нет в запросе
        if incoming_search_row_ids and search_rows_data:
            # Удаляем строки только если есть incoming_search_row_ids И search_rows_data не пустой
            # Это предотвращает удаление всех строк, когда search_rows_data не передается в запросе
            SearchRow.objects.filter(project=project).exclude(id__in=incoming_search_row_ids).delete()
        else:
            # Если incoming_search_row_ids пустой или search_rows_data пустой, 
            # значит мы не должны удалять существующие строки
            print(f"Предотвращено удаление строк поиска для проекта {project.id}: обновление не содержит данных о строках поиска")
        
        # Обновление existing search rows
        for search_row_data in search_rows_data:
            # Если в данных есть ID, то это существующая запись, которую нужно обновить
            if 'id' in search_row_data and search_row_data['id']:
                try:
                    search_row = SearchRow.objects.get(id=search_row_data['id'], project=project)
                    for attr, value in search_row_data.items():
                        setattr(search_row, attr, value)
                    search_row.save()
                except SearchRow.DoesNotExist:
                    # Если строка с таким ID не найдена, создаем новую
                    search_row_data['project'] = project
                    SearchRow.objects.create(**search_row_data)
            else:
                # Если ID нет, значит, это новая запись
                search_row_data['project'] = project
                SearchRow.objects.create(**search_row_data)
        
        # Обновление existing search criteria
        for search_criterion_data in search_criteria_data:
            search_criterion = project.search_criteria.first()
            if search_criterion:
                for attr, value in search_criterion_data.items():
                    setattr(search_criterion, attr, value)
                search_criterion.save()
            else:
                search_criterion_data['project'] = project
                SearchCriteria.objects.create(**search_criterion_data)

        return project
    

class CandidateExportSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )     

    class Meta:
        model = Candidate
        fields = [
            'hh_url',
            'questions',
            'google_docs_file_id',
            'hh_resume_id',
            'answers',
            'username',
            'user_id',
            'interview_date',
            'title',
            'salary',
        ]


class AnalysisStatisticsExportSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
    )  
    total_resumes = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    analyzed_resumes = serializers.SerializerMethodField()
    pending_resumes = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    average_processing_time = serializers.SerializerMethodField()
    error_count = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    category_distribution = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisStatistics
        fields = [
            'id',

            'project',

            'total_resumes',
            'analyzed_resumes',
            'pending_resumes',
            'last_updated',
            'average_processing_time',
            'error_count',
            'completion_percentage',
            'category_distribution',
        ]

    def get_total_resumes(self, obj: AnalysisStatistics):
        return obj.get_total_resumes()
    
    def get_analyzed_resumes(self, obj: AnalysisStatistics):
        return obj.get_analyzed_resumes()
    
    def get_pending_resumes(self, obj: AnalysisStatistics):
        return obj.get_pending_resumes()
    
    def get_last_updated(self, obj: AnalysisStatistics):
        last_updated = obj.get_last_updated()
        return last_updated.strftime('%H:%M %d.%m.%Y') if last_updated else '-'
    
    def get_average_processing_time(self, obj: AnalysisStatistics):
        return obj.get_average_processing_time()
    
    def get_error_count(self, obj: AnalysisStatistics):
        return obj.get_error_count()
    
    def get_completion_percentage(self, obj: AnalysisStatistics):
        return obj.get_completion_percentage()

    def get_category_distribution(self, obj: AnalysisStatistics):
        return obj.get_category_distribution()
    

class PromptsSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=False,
    )

    class Meta:
        model = Prompt
        fields = [
            'id',

            'project',

            'description',
            'system',
            'user',
        ]


class ProjectMetaDataSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
    )

    class Meta:
        model = ProjectMetaData
        fields = [
            'id',
            'project',
            'position',
            'location',
            'salary_type',
            'salary',
            'payment_method',
            'work_format',
            'employment_type',
            'experience',
            'comment',
        ]


class HHAreaSerializer(serializers.ModelSerializer):
    """Сериализатор для модели HHArea"""
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = HHArea
        fields = ['id', 'hh_id', 'name', 'parent', 'parent_name']
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None