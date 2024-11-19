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

    class Meta:
        model = SearchCriteria
        fields = [
            'id', 
            'must_have', 
            'nice_to_have',
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
    search_rows = SearchRowSerializer(many=True)
    search_criteria = SearchCriteriaSerializer(many=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'status',
            'name',
            'created_by',
            'created_at',
            'description',

            'search_rows',
            'search_criteria',
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
        print('validated_data', validated_data)
        search_rows_data = validated_data.pop('search_rows', [])
        search_criteria_data = validated_data.pop('search_criteria', [])
        
        project = super().update(instance, validated_data)

        # Обновление existing search rows
        for search_row_data in search_rows_data:
            print('search_row_data', search_row_data)
            # Если в данных есть ID, то это существующая запись, которую нужно обновить
            if 'id' in search_row_data:
                search_row = SearchRow.objects.get(id=search_row_data['id'], project=project)
                if search_row:
                    for attr, value in search_row_data.items():
                        setattr(search_row, attr, value)
                    search_row.save()
            else:
                # Если ID нет, значит, это новая запись
                search_row_data['project'] = project.id
                search_row_serializer = SearchRowSerializer(data=search_row_data)
                if search_row_serializer.is_valid():
                    search_row_serializer.save()
        
        # Обновление existing search criteria
        for search_criterion_data in search_criteria_data:
            print('search_criterion_data', search_criterion_data)
            search_criterion = project.search_criteria.first()
            if search_criterion:
                for attr, value in search_criterion_data.items():
                    setattr(search_criterion, attr, value)
                search_criterion.save()
            else:
                search_criterion_data['project'] = project.id
                search_criterion_serializer = SearchCriteriaSerializer(data=search_criterion_data)
                if search_criterion_serializer.is_valid():
                    search_criterion_serializer.save()

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
        ]

    def get_total_resumes(self, obj: AnalysisStatistics):
        return obj.get_total_resumes()
    
    def get_analyzed_resumes(self, obj: AnalysisStatistics):
        return obj.get_analyzed_resumes()
    
    def get_pending_resumes(self, obj: AnalysisStatistics):
        return obj.get_pending_resumes()
    
    def get_last_updated(self, obj: AnalysisStatistics):
        return obj.get_last_updated()
    
    def get_average_processing_time(self, obj: AnalysisStatistics):
        return obj.get_average_processing_time()
    
    def get_error_count(self, obj: AnalysisStatistics):
        return obj.get_error_count()
    
    def get_completion_percentage(self, obj: AnalysisStatistics):
        return obj.get_completion_percentage()