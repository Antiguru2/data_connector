import requests
import json
from django.urls import reverse
from django.conf import settings

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework import (
    status,
    permissions,
)

from main.mixins import (
    ViewSetAndFilterByGetParamsMixin,
)
from talent_finder.models import (
    SearchRow,
    SearchCriteria,
    Project, 
    Candidate, 
    AnalysisStatistics,
    Prompt,
    ProjectMetaData,
    HHArea,
    AITask,
    AITaskLog,
)
from data_connector.export_serializers.neuro_screener_serializers import (
    ProjectExportSerializer,
    SearchCriteriaSerializer, 
    AnalysisStatisticsExportSerializer,
    PromptsSerializer,
    SearchRowSerializer,
    ProjectMetaDataSerializer,
    HHAreaSerializer,
    AITaskSerializer,
)
from data_connector.import_serializers.neuro_screener_serializers import CandidateImportSerializer


class IsStaffPermission(permissions.BasePermission):
    """
    Разрешение, которое позволяет доступ только пользователям с is_staff=True.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff
    

class DemoUserPermission(permissions.BasePermission):
    """
    Разрешение, которое позволяет доступ только пользователям с is_staff=True.
    """

    def has_permission(self, request, view):
        print('DemoUserPermission.has_permission()')
        print('request.user', request.user)
        print('demo_users in ...', 'demo_users' in request.user.groups.values_list('name', flat=True))
        return request.user and 'demo_users' in request.user.groups.values_list('name', flat=True)
    

class ProjectsModelViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectExportSerializer
    # permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]

    def list(self, request, *args, **kwargs):
        queryset = Project.objects.none()
        if request.user:
            queryset = self.get_queryset().filter(
                created_by=request.user
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer: ProjectExportSerializer = self.get_serializer(data=request.data)
        if not request.user.is_authenticated:
            return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        serializer.initial_data['created_by'] = request.user.id
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    # def update(self, request, *args, **kwargs):
    #     return super().update(request, *args, **kwargs)
    

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Установить размер страницы по умолчанию
    page_size_query_param = 'page_size'  # Параметр для указания размера страницы
    max_page_size = 100  # Максимально допустимый размер страницы

    def get_paginated_response(self, data):
        try:
            next = self.page.next_page_number()
        except:
            next = None

        try:
            previous = self.page.previous_page_number()
        except:
            previous = None

        return Response({
            'links': {
                'next': next,
                'previous': previous
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'results': data
        })


class CandidateModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = Candidate.objects.all().order_by('is_viewed')
    serializer_class = CandidateImportSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]


class AnalysisStatisticsModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = AnalysisStatistics.objects.all()
    serializer_class = AnalysisStatisticsExportSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]

    @action(detail=False, methods=['get'])
    def retrieve_last(self, request):
        project_id = request.GET.get('project_id')
        if not project_id:
            return Response({"message": "Project ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        analysis_statistics = AnalysisStatistics.objects.filter(project_id=project_id).order_by('-created_at').first()
        if not analysis_statistics:
            return Response({"message": "Analysis statistics not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(analysis_statistics)
        return Response(serializer.data)


class SearchCriteriaModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = SearchCriteria.objects.all()
    serializer_class = SearchCriteriaSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]


class SearchRowModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = SearchRow.objects.all()
    serializer_class = SearchRowSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]


class PromptsModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = Prompt.objects.all()
    serializer_class = PromptsSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]


class ProjectMetaDataModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = ProjectMetaData.objects.all()
    serializer_class = ProjectMetaDataSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]

    @action(detail=False, methods=['post'])
    def create_for_project(self, request):
        """
        Создает или обновляет метаданные для указанного проекта.
        """
        project_id = request.data.get('project')
        if not project_id:
            return Response({"message": "Project ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": f"Project with ID {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, существуют ли уже метаданные для этого проекта
        try:
            meta = ProjectMetaData.objects.get(project=project)
            # Если метаданные существуют, обновляем их
            serializer = self.get_serializer(meta, data=request.data, partial=True)
        except ProjectMetaData.DoesNotExist:
            # Если метаданных нет, создаем новые
            serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


class HHAreaModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = HHArea.objects.all()
    serializer_class = HHAreaSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def root_areas(self, request):
        """Получить только корневые регионы (страны)"""
        areas = HHArea.objects.filter(parent__isnull=True)
        serializer = self.get_serializer(areas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='child/(?P<parent_id>[^/.]+)')
    def child_areas(self, request, parent_id=None):
        """Получить дочерние регионы для указанного родительского региона"""
        areas = HHArea.objects.filter(parent_id=parent_id)
        serializer = self.get_serializer(areas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Поиск регионов по названию.
        Параметры:
        - q: строка поиска
        - limit: максимальное количество результатов (по умолчанию 10)
        """
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        
        if not query:
            return Response([])
        
        areas = HHArea.objects.filter(name__icontains=query)[:limit]
        serializer = self.get_serializer(areas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """
        Получить все регионы без пагинации.
        Внимание: может возвращать большой объем данных!
        """
        areas = HHArea.objects.all()
        serializer = self.get_serializer(areas, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def get_names_by_ids(self, request):
        """
        Получить названия регионов по их ID.
        Параметры:
        - ids: список ID регионов, разделенных запятыми
        """
        ids_param = request.query_params.get('ids', '')
        if not ids_param:
            return Response([])
            
        # Разбиваем строку с ID на список
        ids = [int(id_str) for id_str in ids_param.split(',') if id_str.strip().isdigit()]
        
        if not ids:
            return Response([])
            
        # Получаем регионы по ID
        areas = HHArea.objects.filter(id__in=ids)
        
        # Формируем результат в виде словаря {id: name}
        result = {area.id: {
            'name': area.name,
            'hh_id': area.hh_id,
            'full_name': area.full_name
        } for area in areas}
        
        return Response(result)


class AITaskModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = AITask.objects.all()
    serializer_class = AITaskSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_for_project(self, request):
        """
        Создает новую задачу для указанного проекта.
        """
        project_id = request.data.get('project_id')
        task_type = request.data.get('task_type')
        
        if not project_id:
            return Response(
                {"error": "Project ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not task_type:
            return Response(
                {"error": "Task type is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": f"Project with ID {project_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Создаем новую задачу
        task = AITask.objects.create(
            project=project,
            task_type=task_type,
            status=AITask.STATUS_PENDING,
            progress=0
        )
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message=f"Задача {task.get_task_type_display()} создана",
            level='info'
        )
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_search_criteria(self, request):
        """
        Создает задачу генерации поисковых критериев для указанного проекта.
        """
        project_id = request.data.get('project_id')
        
        if not project_id:
            return Response(
                {"error": "Project ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": f"Project with ID {project_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Создаем новую задачу
        task = AITask.objects.create(
            project=project,
            task_type=AITask.TASK_TYPE_SEARCH_CRITERIA_GENERATION,
            status=AITask.STATUS_PENDING,
            progress=0
        )
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message="Задача генерации поисковых критериев создана",
            level='info'
        )
        
        # Отправляем запрос в n8n для генерации поисковых критериев
        try:
            # Получаем метаданные проекта
            meta = ProjectMetaData.objects.get(project=project)
            
            # Формируем данные для запроса
            webhook_url = "https://n8n.innoprompt.ru/webhook/f07f3ee0-af32-4136-9670-1b8904f4226f"
            payload = {
                "task_id": task.id,
                "project_id": project.id,
                "position": meta.position,
                "location": meta.location,
                "salary_type": meta.salary_type,
                "salary": meta.salary,
                "payment_method": meta.payment_method,
                "work_format": meta.work_format,
                "employment_type": meta.employment_type,
                "experience": meta.experience,
                "comment": meta.comment
            }
            
            # Отправляем запрос
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"n8n вернул код ошибки: {response.status_code}")
            
            # Обновляем статус задачи
            task.status = AITask.STATUS_IN_PROGRESS
            task.started_at = timezone.now()
            task.save()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message="Запрос на генерацию поисковых критериев отправлен",
                level='info'
            )
            
            serializer = self.get_serializer(task)
            return Response(serializer.data)
            
        except Exception as e:
            # Если произошла ошибка, отмечаем задачу как неудачную
            task.status = AITask.STATUS_FAILED
            task.error_message = str(e)
            task.save()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Ошибка при отправке запроса: {str(e)}",
                level='error'
            )
            
            return Response(
                {"error": f"Failed to start search criteria generation: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Получает статус задачи.
        """
        try:
            task = self.get_object()
        except AITask.DoesNotExist:
            return Response(
                {"error": f"Task with ID {pk} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Получаем последние логи задачи
        logs = AITaskLog.objects.filter(task=task).order_by('-timestamp')[:10].values('message', 'level', 'timestamp')
        
        # Формируем ответ
        response_data = {
            "id": task.id,
            "project_id": task.project.id,
            "task_type": task.task_type,
            "task_type_display": task.get_task_type_display(),
            "status": task.status,
            "status_display": task.get_status_display(),
            "progress": task.progress,
            "message": task.message,
            "logs": list(logs),
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }
        
        # Если задача завершена, добавляем результаты
        if task.status == AITask.STATUS_COMPLETED and task.result_data:
            response_data["result"] = task.result_data
        
        # Если задача завершилась с ошибкой, добавляем сообщение об ошибке
        if task.status == AITask.STATUS_FAILED and task.error_message:
            response_data["error"] = task.error_message
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """
        Обновляет прогресс выполнения задачи.
        """
        try:
            task = self.get_object()
        except AITask.DoesNotExist:
            return Response(
                {"error": f"Task with ID {pk} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        progress = request.data.get('progress')
        message = request.data.get('message')
        
        if progress is not None:
            task.progress = progress
        
        if message:
            task.message = message
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=message,
                level='info'
            )
        
        # Если задача еще не в процессе, обновляем статус
        if task.status == AITask.STATUS_PENDING:
            task.status = AITask.STATUS_IN_PROGRESS
            task.started_at = timezone.now()
        
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Отмечает задачу как завершенную.
        """
        try:
            task = self.get_object()
        except AITask.DoesNotExist:
            return Response(
                {"error": f"Task with ID {pk} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        result_data = request.data.get('result')
        message = request.data.get('message', "Задача успешно завершена")
        
        task.status = AITask.STATUS_COMPLETED
        task.progress = 100
        task.message = message
        task.completed_at = timezone.now()
        
        if result_data:
            task.result_data = result_data
        
        task.save()
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message=message,
            level='success'
        )
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """
        Отмечает задачу как неудачную.
        """
        try:
            task = self.get_object()
        except AITask.DoesNotExist:
            return Response(
                {"error": f"Task with ID {pk} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        error_message = request.data.get('error', "Неизвестная ошибка")
        
        task.status = AITask.STATUS_FAILED
        task.error_message = error_message
        task.completed_at = timezone.now()
        task.save()
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message=f"Ошибка: {error_message}",
            level='error'
        )
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def save_search_criteria(self, request, pk=None):
        """
        Сохраняет сгенерированные поисковые критерии для проекта.
        """
        try:
            task = self.get_object()
        except AITask.DoesNotExist:
            return Response(
                {"error": f"Task with ID {pk} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        criteria_data = request.data.get('criteria')
        if not criteria_data:
            return Response(
                {"error": "Criteria data is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Получаем или создаем критерии поиска для проекта
            criteria, created = SearchCriteria.objects.get_or_create(
                project=task.project,
                defaults={
                    'must_have': criteria_data.get('must_have', ''),
                    'nice_to_have': criteria_data.get('nice_to_have', ''),
                    'additional': criteria_data.get('additional', ''),
                    'areas': criteria_data.get('areas', [])
                }
            )
            
            # Если критерии уже существуют, обновляем их
            if not created:
                criteria.must_have = criteria_data.get('must_have', '')
                criteria.nice_to_have = criteria_data.get('nice_to_have', '')
                criteria.additional = criteria_data.get('additional', '')
                criteria.areas = criteria_data.get('areas', [])
                criteria.save()
            
            # Обновляем задачу
            task.complete({'criteria': criteria_data})
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Поисковые критерии успешно сохранены",
                level='success'
            )
            
            return Response({"success": True})
        except Exception as e:
            # Если произошла ошибка, отмечаем задачу как неудачную
            error_message = f"Ошибка при сохранении поисковых критериев: {str(e)}"
            task.fail(error_message)
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
            
            return Response(
                {"error": error_message}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='project/(?P<project_id>[^/.]+)/resume-analysis-status')
    def get_task_status_for_project(self, request, project_id=None):
        """
        Получает статус задачи анализа резюме для указанного проекта.
        Используется для отслеживания прогресса анализа резюме.
        """
        if not project_id:
            return Response(
                {"error": "Project ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": f"Project with ID {project_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Получаем последнюю задачу анализа резюме для проекта
        task = AITask.objects.filter(
            project=project,
            task_type=AITask.TASK_TYPE_RESUME_ANALYSIS
        ).order_by('-created_at').first()
        
        if not task:
            return Response({
                "status": "not_started",
                "progress": 0,
                "message": "Анализ резюме еще не начат",
                "logs": []
            })
        
        # Получаем последние логи задачи
        logs = AITaskLog.objects.filter(task=task).order_by('-timestamp')[:10].values('message', 'level', 'timestamp')
        
        # Формируем ответ
        response_data = {
            "status": task.status,
            "progress": task.progress / 100.0,  # Преобразуем в диапазон от 0 до 1
            "message": task.message or f"Статус: {task.get_status_display()}",
            "logs": list(logs),
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }
        
        # Если задача завершена, добавляем результаты
        if task.status == AITask.STATUS_COMPLETED and task.result_data:
            response_data["result"] = task.result_data
        
        # Если задача завершилась с ошибкой, добавляем сообщение об ошибке
        if task.status == AITask.STATUS_FAILED and task.error_message:
            response_data["error"] = task.error_message
        
        return Response(response_data)
