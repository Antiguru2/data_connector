import requests
import json
from django.urls import reverse
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

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
            ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        
        serializer.initial_data['created_by'] = request.user.id
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    # def update(self, request, *args, **kwargs):
    #     return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='clear_search_rows')
    def clear_search_rows(self, request, pk=None):
        """
        Удаляет все поисковые строки для указанного проекта.
        Возвращает количество удаленных строк.
        """
        try:
            project = self.get_object()
            count = project.search_rows.all().delete()[0]
            return Response({
                'status': 'success',
                'message': f'Удалено {count} поисковых строк',
                'count': count
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='statistics')
    def get_project_statistics(self, request, pk=None):
        """
        Получение статистики проекта для нового интерфейса
        """
        try:
            project = self.get_object()
            
            # Получаем общее количество резюме
            total_resumes = Candidate.objects.filter(project=project).count()
            
            # Получаем количество проанализированных резюме
            analyzed_resumes = Candidate.objects.filter(
                project=project, 
                category__in=['suitable', 'possibly_suitable', 'not_suitable']
            ).count()
            
            # Получаем количество ожидающих анализа резюме
            pending_resumes = Candidate.objects.filter(
                project=project, 
                category='not_analyzed'
            ).count()
            
            # Вычисляем процент завершения
            completion_percentage = 0
            if total_resumes > 0:
                completion_percentage = round((analyzed_resumes / total_resumes) * 100)
            
            # Получаем распределение по категориям
            category_distribution = {
                'suitable': Candidate.objects.filter(project=project, category='suitable').count(),
                'possibly_suitable': Candidate.objects.filter(project=project, category='possibly_suitable').count(),
                'not_suitable': Candidate.objects.filter(project=project, category='not_suitable').count(),
                'not_analyzed': Candidate.objects.filter(project=project, category='not_analyzed').count()
            }
            
            # Получаем время последнего обновления
            last_updated = None
            latest_candidate = Candidate.objects.filter(project=project).order_by('-updated_at').first()
            if latest_candidate:
                last_updated = latest_candidate.updated_at
            
            # Формируем ответ
            response_data = {
                'total_resumes': total_resumes,
                'analyzed_resumes': analyzed_resumes,
                'pending_resumes': pending_resumes,
                'completion_percentage': completion_percentage,
                'category_distribution': category_distribution,
                'last_updated': last_updated
            }
            
            return Response(response_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='candidates')
    def get_project_candidates(self, request, pk=None):
        """
        Получение списка кандидатов проекта с возможностью фильтрации и поиска
        """
        try:
            project = self.get_object()
            
            # Получаем параметры фильтрации
            category = request.query_params.get('category', None)
            search_query = request.query_params.get('search', None)
            
            # Формируем базовый запрос
            candidates = Candidate.objects.filter(project=project)
            
            # Применяем фильтр по категории
            if category:
                candidates = candidates.filter(category=category)
            
            # Применяем поиск
            if search_query:
                candidates = candidates.filter(
                    Q(candidat_full_name__icontains=search_query) | 
                    Q(resume_title__icontains=search_query) |
                    Q(experience_text__icontains=search_query) |
                    Q(comment__icontains=search_query)
                )
            
            # Сортируем результаты
            candidates = candidates.order_by('-updated_at')
            
            # Пагинация
            paginator = PageNumberPagination()
            paginator.page_size = 12  # Количество кандидатов на странице
            paginated_candidates = paginator.paginate_queryset(candidates, request)
            
            # Сериализуем данные
            serializer = CandidateImportSerializer(paginated_candidates, many=True)
            
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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

        # Измените здесь, чтобы настроить, какие данные будут возвращены
        return Response({
            'count': self.page.paginator.count,  # Общее количество объектов
            'next': next,  # URL следующей страницы
            'previous': previous,  # URL предыдущей страницы
            'results': data,  # Отфильтрованные результаты
            # Можете добавить дополнительные поля по своему усмотрению
            'page_size': self.page_size,
            'current_page': self.page.number,
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

    @action(detail=False, methods=['get'], url_path='last')
    def retrieve_last(self, request):
        project_id = request.query_params.get('project_id')
        last_analysis = self.queryset.filter(project_id=project_id).order_by('created_at').last()
        serializer = self.get_serializer(last_analysis)
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
    
    @action(detail=False, methods=['get'], url_path='project/(?P<project_id>\d+)')
    def get_by_project(self, request, project_id=None):
        try:
            meta_data = ProjectMetaData.objects.get(project_id=project_id)
            serializer = self.get_serializer(meta_data)
            return Response(serializer.data)
        except ProjectMetaData.DoesNotExist:
            return Response(
                {
                    'position': '',
                    'location': '',
                    'salary_type': 'fixed',
                    'salary': '',
                    'payment_method': 'cash',
                    'work_format': '',
                    'employment_type': '',
                    'experience': '',
                    'comment': ''
                },
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=['post'], url_path='update-for-project/(?P<project_id>\d+)')
    def update_for_project(self, request, project_id=None):
        try:
            meta_data = ProjectMetaData.objects.get(project_id=project_id)
            serializer = self.get_serializer(meta_data, data=request.data, partial=True)
        except ProjectMetaData.DoesNotExist:
            serializer = self.get_serializer(data={**request.data, 'project': project_id})

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create-for-project')
    def create_for_project(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HHAreaModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = HHArea.objects.all()
    serializer_class = HHAreaSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='root-areas')
    def root_areas(self, request):
        """Получить только корневые регионы (страны)"""
        areas = self.queryset.filter(parent=None)
        serializer = self.get_serializer(areas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='child-areas/(?P<parent_id>\d+)')
    def child_areas(self, request, parent_id=None):
        """Получить дочерние регионы для указанного родительского региона"""
        areas = self.queryset.filter(parent_id=parent_id)
        serializer = self.get_serializer(areas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='popular')
    def popular_cities(self, request):
        """
        Получить список популярных городов для быстрого выбора.
        Возвращает города, у которых установлен флаг is_popular=True.
        """
        popular_cities = self.queryset.filter(is_popular=True).order_by('name')
        serializer = self.get_serializer(popular_cities, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Поиск городов по запросу пользователя.
        Ищет города, название которых начинается с введенного запроса.
        Популярные города (отмеченные в админке) выводятся первыми.
        """
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response([])
        
        # Преобразуем первую букву запроса в верхний регистр, остальные - в нижний
        # Это поможет найти города, которые начинаются с введенного запроса
        capitalized_query = query[0].upper() + query[1:].lower()
        
        # Поиск по началу названия города
        queryset = HHArea.objects.filter(
            name__startswith=capitalized_query
        ).select_related('parent')
        
        # Если нет результатов, пробуем поиск по содержанию
        if queryset.count() == 0:
            queryset = HHArea.objects.filter(
                name__icontains=query
            ).select_related('parent')
        
        # Сортируем результаты: сначала популярные города, затем остальные
        # Используем order_by для сортировки: сначала по is_popular (в обратном порядке), затем по имени
        queryset = queryset.order_by('-is_popular', 'name')
        
        # Ограничиваем результаты для производительности
        queryset = queryset[:20]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """
        Получить все регионы без пагинации.
        Внимание: может возвращать большой объем данных!
        """
        # Можно добавить фильтрацию, например, только для российских городов
        queryset = self.queryset.filter(parent__parent__name='Россия')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='get_names_by_ids')
    def get_names_by_ids(self, request):
        """
        Получить имена регионов по их ID.
        Принимает параметр ids в виде строки с разделителями-запятыми или списка ID.
        Возвращает словарь, где ключ - ID региона, значение - его имя.
        """
        ids_param = request.query_params.get('ids', '')
        
        # Проверяем, что параметр не пустой
        if not ids_param:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        
        # Преобразуем строку с ID в список
        if isinstance(ids_param, str):
            # Если передан один ID без запятой
            if ',' not in ids_param:
                ids = [ids_param]
            else:
                ids = ids_param.split(',')
        else:
            ids = ids_param
        
        # Очищаем список от пустых значений и преобразуем в целые числа
        ids = [int(id_str) for id_str in ids if id_str.strip()]
        
        # Получаем регионы по ID
        areas = HHArea.objects.filter(id__in=ids)
        
        # Формируем словарь {id: name}
        result = {}
        for area in areas:
            result[str(area.id)] = area.name
        
        return Response(result)


class AITaskModelViewSet(
    ViewSetAndFilterByGetParamsMixin,
    ModelViewSet,
):
    queryset = AITask.objects.all()
    serializer_class = AITaskSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [
        permissions.IsAuthenticated, 
        DemoUserPermission or IsStaffPermission,
    ]
    
    @action(detail=False, methods=['post'], url_path='create-for-project')
    def create_for_project(self, request):
        """
        Создает новую задачу ИИ для указанного проекта.
        """
        project_id = request.data.get('project')
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
        serializer = self.get_serializer(data={
            'project': project_id,
            'task_type': task_type,
            'status': AITask.STATUS_PENDING,
        })
        
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        # Если это задача генерации поисковых запросов, отправляем запрос в n8n
        if task_type == AITask.TASK_TYPE_SEARCH_QUERY_GENERATION:
            # Запускаем задачу в фоновом режиме
            self.start_search_query_generation(task, project)
        # Если это задача создания команды оценки, отправляем запрос в n8n
        elif task_type == AITask.TASK_TYPE_EVALUATORS_TEAM_CREATION:
            # Запускаем задачу в фоновом режиме
            self.start_evaluators_team_creation(task, project)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='update-progress')
    def update_progress(self, request, pk=None):
        """
        Обновляет прогресс выполнения задачи.
        Используется для обратного вызова из n8n.
        """
        task = self.get_object()
        progress = request.data.get('progress')
        message = request.data.get('message')
        
        if progress is None:
            return Response(
                {"error": "Progress is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.update_progress(progress, message)
        
        # Создаем запись в логе
        if message:
            AITaskLog.objects.create(
                task=task,
                message=message,
                level='info'
            )
        
        return Response(self.get_serializer(task).data)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_task(self, request, pk=None):
        """
        Отмечает задачу как завершенную.
        Используется для обратного вызова из n8n.
        """
        task = self.get_object()
        import logging
        logger = logging.getLogger(__name__)
        
        # Добавляем подробное логирование входящих данных для отладки
        logger.info(f"[DEBUG] Получены данные для complete_task задачи {task.id}: {request.data}")
        AITaskLog.objects.create(
            task=task,
            message=f"Получены данные от n8n: {request.data}",
            level='info'
        )
        
        try:
            # Получаем данные из запроса
            result_data = request.data.get('result_data')
            search_rows_data = request.data.get('search_rows')
            
            logger.info(f"[DEBUG] result_data type: {type(result_data)}, значение: {result_data}")
            
            # Если это задача создания команды оценки
            if task.task_type == AITask.TASK_TYPE_EVALUATORS_TEAM_CREATION:
                logger.info(f"[DEBUG] Обрабатываем задачу создания команды оценки {task.id}")
                logger.info(f"[DEBUG] result_data is list: {isinstance(result_data, list)}")
                
                # Проверяем все доступные поля в запросе
                for key, value in request.data.items():
                    logger.info(f"[DEBUG] Поле {key} в запросе: {value}")
                    if key != 'result_data' and isinstance(value, list):
                        logger.info(f"[DEBUG] Обнаружен список в поле {key}")
                
                # Проверяем различные варианты структуры данных
                prompts_to_save = None
                
                if isinstance(result_data, list):
                    logger.info(f"[DEBUG] result_data это список, сохраняем его")
                    prompts_to_save = result_data
                elif isinstance(result_data, dict) and 'json_prompts' in result_data:
                    logger.info(f"[DEBUG] json_prompts найден в result_data")
                    prompts_to_save = result_data['json_prompts']
                elif isinstance(result_data, dict) and 'prompts' in result_data:
                    logger.info(f"[DEBUG] prompts найден в result_data")
                    prompts_to_save = result_data['prompts']
                elif 'json_prompts' in request.data:
                    logger.info(f"[DEBUG] json_prompts найден в корне запроса")
                    prompts_to_save = request.data['json_prompts']
                elif 'prompts' in request.data:
                    logger.info(f"[DEBUG] prompts найден в корне запроса")
                    prompts_to_save = request.data['prompts']
                
                # Дополнительная проверка найденных промптов
                if prompts_to_save:
                    logger.info(f"[DEBUG] Найдены промпты для сохранения: {prompts_to_save}")
                    
                    # Сохраняем промпты в проект
                    project_id = task.project.id
                    task.project.json_prompts = prompts_to_save
                    task.project.save()
                    
                    logger.info(f"[DEBUG] Промпты сохранены в проект {task.project.id}")
                    logger.info(f"[DEBUG] Проверка сохранения - промпты в проекте: {task.project.json_prompts}")
                    
                    # Получаем проект заново из БД для проверки сохранения
                    from talent_finder.models import Project
                    refreshed_project = Project.objects.get(id=project_id)
                    logger.info(f"[DEBUG] Проект после перезагрузки из БД - id: {refreshed_project.id}")
                    logger.info(f"[DEBUG] Промпты в проекте после перезагрузки из БД: {refreshed_project.json_prompts}")
                    
                    # Проверяем с помощью SQL
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT json_prompts FROM talent_finder_project WHERE id = %s", [project_id])
                        row = cursor.fetchone()
                        logger.info(f"[DEBUG] Промпты в БД напрямую: {row[0]}")
                    
                    AITaskLog.objects.create(
                        task=task,
                        message=f"Промпты успешно сохранены в проект: {prompts_to_save}",
                        level='success'
                    )
                else:
                    logger.error(f"[DEBUG] Не удалось найти промпты для сохранения в проект")
                    AITaskLog.objects.create(
                        task=task,
                        message="Не удалось найти промпты для сохранения в проект",
                        level='error'
                    )
            
            # Если это задача генерации поисковых запросов
            elif task.task_type == AITask.TASK_TYPE_SEARCH_QUERY_GENERATION:
                logger.info(f"[DEBUG] Обрабатываем задачу генерации поисковых запросов {task.id}")
                # Проверяем наличие search_rows в разных местах
                if search_rows_data:
                    logger.info(f"[DEBUG] search_rows_data найдено в корне запроса")
                    self.save_search_rows(task.project, search_rows_data, task)
                elif isinstance(result_data, dict) and 'search_rows' in result_data:
                    logger.info(f"[DEBUG] search_rows найдено в result_data")
                    self.save_search_rows(task.project, result_data['search_rows'], task)
                elif isinstance(result_data, list) and len(result_data) > 0 and isinstance(result_data[0], dict) and 'search_rows' in result_data[0]:
                    logger.info(f"[DEBUG] search_rows найдено в первом элементе списка result_data")
                    self.save_search_rows(task.project, result_data[0]['search_rows'], task)
                else:
                    logger.error(f"[DEBUG] Не найдены данные search_rows в запросе")
                    AITaskLog.objects.create(
                        task=task,
                        message="Не найдены данные search_rows в запросе",
                        level='warning'
                    )
                
        except Exception as e:
            error_message = f"Ошибка при обработке данных: {str(e)}"
            logger.exception(f"[DEBUG] {error_message}")
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
            result_data = {}
        
        # Отмечаем задачу как завершенную
        task.complete(result_data or {})
        
        # Проверяем, сохранились ли данные в проекте
        if task.task_type == AITask.TASK_TYPE_EVALUATORS_TEAM_CREATION:
            from talent_finder.models import Project
            task.project.refresh_from_db()
            logger.info(f"[DEBUG] После complete - промпты в проекте: {task.project.json_prompts}")
            
            # Еще одна проверка после complete
            refreshed_project = Project.objects.get(id=task.project.id)
            logger.info(f"[DEBUG] После complete - получили проект из БД: {refreshed_project.id}")
            logger.info(f"[DEBUG] После complete - промпты в перезагруженном проекте: {refreshed_project.json_prompts}")
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message=f"Задача успешно завершена",
            level='success'
        )
        
        return Response(self.get_serializer(task).data)
    
    @action(detail=True, methods=['post'], url_path='fail')
    def fail_task(self, request, pk=None):
        """
        Отмечает задачу как неудачную.
        Используется для обратного вызова из n8n.
        """
        task = self.get_object()
        error_message = request.data.get('error_message', 'Неизвестная ошибка')
        
        task.fail(error_message)
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message=f"Задача завершилась с ошибкой: {error_message}",
            level='error'
        )
        
        return Response(self.get_serializer(task).data)
    
    @action(detail=False, methods=['get'], url_path='project/(?P<project_id>\d+)')
    def get_tasks_for_project(self, request, project_id=None):
        """
        Получает все задачи для указанного проекта.
        """
        tasks = self.queryset.filter(project_id=project_id)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='project/(?P<project_id>\d+)/latest/(?P<task_type>[a-z_]+)')
    def get_latest_task(self, request, project_id=None, task_type=None):
        """
        Получает последнюю задачу указанного типа для проекта.
        """
        try:
            task = self.queryset.filter(
                project_id=project_id, 
                task_type=task_type
            ).latest('created_at')
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except AITask.DoesNotExist:
            return Response(
                {"error": f"No tasks of type {task_type} found for project {project_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'], url_path='status')
    def get_status(self, request, pk=None):
        """
        Получает текущий статус задачи.
        """
        task = self.get_object()
        
        response_data = {
            'id': task.id,
            'status': task.status,
            'progress': task.progress,
            'status_message': task.message or '',
            'created_at': task.created_at,
            'updated_at': task.updated_at,
        }
        
        if task.status == AITask.STATUS_COMPLETED:
            response_data['result_data'] = task.result_data
        elif task.status == AITask.STATUS_FAILED:
            response_data['error'] = task.error_message
        
        return Response(response_data)

    def start_search_query_generation(self, task, project):
        """
        Запускает процесс генерации поисковых запросов через n8n.
        """
        
        # URL для обратного вызова
        base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
        callback_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/update-progress/"
        complete_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/complete/"
        fail_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/fail/"
        
        # Получаем метаданные проекта
        try:
            meta = project.meta
        except:
            meta = None
        
        # Формируем данные для отправки в n8n
        payload = {
            'project_id': project.id,
            'project_name': project.name,
            'task_id': str(task.id),
            'callback_url': callback_url,
            'complete_url': complete_url,
            'fail_url': fail_url,
            'save_url': complete_url  # Добавляем save_url, используя тот же URL что и для complete_url
        }
        
        # Добавляем метаданные проекта, если они есть
        if meta:
            payload.update({
                'position': meta.position,
                'location': meta.location,
                'salary_type': meta.salary_type,
                'salary': meta.salary,
                'work_format': meta.work_format,
                'employment_type': meta.employment_type,
                'experience': meta.experience,
                'comment': meta.comment
            })
        
        # Добавляем поисковые критерии, если они есть
        search_criteria = project.search_criteria.first()
        if search_criteria:
            payload.update({
                'must_have': search_criteria.must_have,
                'nice_to_have': search_criteria.nice_to_have,
                'additional': search_criteria.additional,
                'areas': search_criteria.areas
            })
        
        # URL вебхука n8n
        n8n_webhook_url = 'https://n8n.innoprompt.ru/webhook/0dcb7fc4-0989-445b-b855-8eaa59acae92'
        
        try:
            # Обновляем задачу - она начала выполняться
            task.start()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Отправка запроса на генерацию поисковых запросов в n8n",
                level='info'
            )
            
            # Отправляем запрос в n8n
            response = requests.post(
                n8n_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # Проверяем ответ
            if response.status_code == 200:
                # Обновляем задачу с внешним ID, если он есть в ответе
                try:
                    response_data = response.json()
                    if 'external_task_id' in response_data:
                        task.external_task_id = response_data['external_task_id']
                        task.save()
                except:
                    pass
                
                # Создаем запись в логе
                AITaskLog.objects.create(
                    task=task,
                    message=f"Запрос успешно отправлен в n8n",
                    level='info'
                )
            else:
                # Если запрос не удался, отмечаем задачу как неудачную
                error_message = f"Ошибка при отправке запроса в n8n: {response.status_code} {response.text}"
                task.fail(error_message)
                
                # Создаем запись в логе
                AITaskLog.objects.create(
                    task=task,
                    message=error_message,
                    level='error'
                )
        except Exception as e:
            # Если произошла ошибка, отмечаем задачу как неудачную
            error_message = f"Ошибка при запуске задачи: {str(e)}"
            task.fail(error_message)
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
    
    def save_search_rows(self, project, search_rows_data, task=None):
        """Сохраняет поисковые строки для проекта"""
        try:
            # Удаляем старые поисковые строки
            project.search_rows.all().delete()
            
            # Создаем новые поисковые строки
            for row_data in search_rows_data:
                # Проверяем наличие необходимых полей или их эквивалентов с префиксом text.
                text = row_data.get('text', '')
                logic = row_data.get('logic', row_data.get('text.logic', 'any'))
                field = row_data.get('field', row_data.get('text.field', 'all'))
                period = row_data.get('period', row_data.get('text.period', 'all_time'))
                
                # Для полей, которые могут быть списками (например, field)
                if not isinstance(field, str):
                    field = 'all'
                
                project.search_rows.create(
                    text=text,
                    logic=logic,
                    field=field,
                    period=period
                )
            
            AITaskLog.objects.create(
                task=task,
                message=f"Поисковые строки успешно сохранены для проекта {project.name}: {search_rows_data}",
                level='success'
            )
        except Exception as e:
            AITaskLog.objects.create(
                task=task,
                message=f"Ошибка при сохранении поисковых строк: {str(e)}",
                level='error'
            )

    @action(detail=False, methods=['post'], url_path='create-search-criteria')
    def create_search_criteria(self, request):
        """
        Создает задачу для формирования поисковых критериев.
        """
        project_id = request.data.get('project')
        
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
        serializer = self.get_serializer(data={
            'project': project_id,
            'task_type': AITask.TASK_TYPE_SEARCH_CRITERIA_GENERATION,
            'status': AITask.STATUS_PENDING,
        })
        
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        # Запускаем задачу в фоновом режиме
        self.start_search_criteria_generation(task, project)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def start_search_criteria_generation(self, task, project):
        """
        Запускает процесс генерации поисковых критериев через n8n.
        """
        
        # URL для обратного вызова
        base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
        callback_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/update-progress/"
        complete_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/complete/"
        save_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/save-search-criteria/"
        fail_url = f"{base_url}{reverse('api-root')}ai_tasks/{task.id}/fail/"
        
        # Получаем метаданные проекта
        try:
            meta = project.meta
        except:
            meta = None
        
        # Формируем данные для отправки в n8n
        payload = {
            'project_id': project.id,
            'project_name': project.name,
            'task_id': str(task.id),
            'callback_url': callback_url,
            'complete_url': complete_url,
            'save_url': save_url,
            'fail_url': fail_url
        }
        
        # Добавляем метаданные проекта, если они есть
        if meta:
            payload.update({
                'position': meta.position,
                'location': meta.location,
                'salary_type': meta.salary_type,
                'salary': meta.salary,
                'work_format': meta.work_format,
                'employment_type': meta.employment_type,
                'experience': meta.experience,
                'comment': meta.comment
            })
        
        # URL вебхука n8n для генерации критериев
        n8n_webhook_url = 'https://n8n.innoprompt.ru/webhook/f07f3ee0-af32-4136-9670-1b8904f4226f'
        
        try:
            # Обновляем задачу - она начала выполняться
            task.start()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Отправка запроса на генерацию поисковых критериев в n8n",
                level='info'
            )
            
            # Отправляем запрос в n8n
            response = requests.post(
                n8n_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # Проверяем ответ
            if response.status_code == 200:
                # Обновляем задачу с внешним ID, если он есть в ответе
                try:
                    response_data = response.json()
                    if 'external_task_id' in response_data:
                        task.external_task_id = response_data['external_task_id']
                        task.save()
                except:
                    pass
                
                # Создаем запись в логе
                AITaskLog.objects.create(
                    task=task,
                    message=f"Запрос успешно отправлен в n8n",
                    level='info'
                )
            else:
                # Если запрос не удался, отмечаем задачу как неудачную
                error_message = f"Ошибка при отправке запроса в n8n: {response.status_code} {response.text}"
                task.fail(error_message)
                
                # Создаем запись в логе
                AITaskLog.objects.create(
                    task=task,
                    message=error_message,
                    level='error'
                )
        except Exception as e:
            # Если произошла ошибка, отмечаем задачу как неудачную
            error_message = f"Ошибка при запуске задачи: {str(e)}"
            task.fail(error_message)
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )

    @action(detail=True, methods=['post'], url_path='save-search-criteria')
    def save_search_criteria(self, request, pk=None):
        """
        Сохраняет поисковые критерии, полученные от n8n.
        """
        task = self.get_object()
        criteria_data = request.data.get('criteria', {})
        
        if not criteria_data:
            return Response(
                {"error": "Criteria data is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Получаем проект
            project = task.project
            
            # Удаляем существующие критерии, если они есть
            project.search_criteria.all().delete()
            
            # Создаем новые критерии
            SearchCriteria.objects.create(
                project=project,
                must_have=criteria_data.get('must_have', ''),
                nice_to_have=criteria_data.get('nice_to_have', ''),
                additional=criteria_data.get('additional', ''),
                areas=criteria_data.get('areas', [])
            )
            
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
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
            
            return Response(
                {"error": error_message}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='analysis-status-for-project/(?P<project_id>[^/.]+)')
    def get_analysis_task_status_for_project(self, request, project_id=None):
        """
        Получение статуса последней задачи анализа резюме для проекта
        """
        try:
            # Находим последнюю задачу анализа резюме для проекта
            task = self.queryset.filter(
                project_id=project_id, 
                task_type='resume_analysis'
            ).order_by('-created_at').first()
            
            if not task:
                return Response({
                    'status': 'not_found',
                    'message': 'Задача анализа резюме не найдена'
                })
            
            # Формируем ответ с информацией о задаче
            response_data = {
                'id': task.id,
                'status': task.status,
                'progress': task.progress,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
            }
            
            return Response(response_data)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=['post'], url_path='update-candidate-status')
    def update_candidate_status(self, request, pk=None):
        """
        Обновляет статус кандидата после анализа.
        Используется для обратного вызова из n8n.
        
        Параметры:
        - candidate_id: ID кандидата, статус которого обновляется
        - category: Категория кандидата (подходит, не подходит, возможно подходит)
        - comment: Комментарий к кандидату
        - vacancy: Вакансия, на которую подходит кандидат
        - skills: Навыки кандидата
        """
        task = self.get_object()
        candidate_id = request.data.get('candidate_id')
        
        if not candidate_id:
            return Response(
                {"error": "Candidate ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Добавляем логирование входящих данных для отладки
        AITaskLog.objects.create(
            task=task,
            message=f"Получены данные от n8n для кандидата {candidate_id}: {request.data}",
            level='info'
        )
        
        try:
            # Находим кандидата
            candidate = Candidate.objects.get(id=candidate_id)
            
            # Обновляем поля кандидата
            update_fields = {}
            
            # Проверяем наличие полей в запросе и добавляем их в словарь обновления
            for field in ['category', 'comment', 'vacancy', 'skills']:
                if field in request.data:
                    update_fields[field] = request.data.get(field)
            
            # Обновляем статусы кандидата
            update_fields['is_analyzed'] = True
            update_fields['is_analyzing'] = False
            
            # Применяем обновления
            for field, value in update_fields.items():
                setattr(candidate, field, value)
            candidate.save()
            
            # Обновляем счетчики в задаче
            result_data = task.result_data or {}
            analyzed_candidates = result_data.get('analyzed_candidates', 0) + 1
            result_data['analyzed_candidates'] = analyzed_candidates
            
            # Обновляем прогресс задачи
            total_candidates = result_data.get('total_candidates', 1)
            progress = min(100, int(analyzed_candidates / total_candidates * 100))
            
            # Обновляем задачу
            task.result_data = result_data
            task.update_progress(
                progress, 
                f"Обработано {analyzed_candidates} из {total_candidates} кандидатов"
            )
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Кандидат {candidate_id} успешно проанализирован",
                level='success'
            )
            
            # Проверяем, остались ли необработанные кандидаты
            if not Candidate.objects.filter(
                project_id=task.project_id,
                is_analyzed=False
            ).exists():
                # Все кандидаты обработаны, завершаем задачу
                task.complete(result_data)
                task.project.status = Project.STATUS_CHOICES[2][0]  # Завершенный статус
                task.project.save()
                
                AITaskLog.objects.create(
                    task=task,
                    message="Все кандидаты обработаны, задача завершена",
                    level='success'
                )
            
            return Response({"status": "success"})
            
        except Candidate.DoesNotExist:
            error_message = f"Кандидат с ID {candidate_id} не найден"
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
            return Response(
                {"error": error_message}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            error_message = f"Ошибка при обновлении статуса кандидата: {str(e)}"
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
            return Response(
                {"error": error_message}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='task-status-for-project/(?P<project_id>[^/.]+)')
    def get_task_status_for_project(self, request, project_id=None):
        """
        Получение статуса последней задачи анализа резюме для проекта
        """
        try:
            # Находим последнюю задачу анализа резюме для проекта
            task = self.queryset.filter(
                project_id=project_id, 
                task_type='resume_analysis'
            ).order_by('-created_at').first()
            
            if not task:
                return Response({
                    'status': 'not_found',
                    'message': 'Задача анализа резюме не найдена'
                })
            
            # Формируем ответ с информацией о задаче
            response_data = {
                'id': task.id,
                'status': task.status,
                'progress': task.progress,
                'created_at': task.created_at,
                'updated_at': task.updated_at
            }
            
            return Response(response_data)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='stop-for-project/(?P<project_id>[^/.]+)')
    def stop_task_for_project(self, request, project_id=None):
        """
        Остановка текущей задачи анализа резюме для проекта
        """
        try:
            # Находим последнюю активную задачу анализа резюме для проекта
            task = self.queryset.filter(
                project_id=project_id, 
                task_type='resume_analysis',
                status='in_progress'
            ).order_by('-created_at').first()
            
            if not task:
                return Response({
                    'status': 'not_found',
                    'message': 'Активная задача анализа резюме не найдена'
                })
            
            # Отмечаем задачу как остановленную
            task.status = 'failed'
            task.error_message = 'Задача остановлена пользователем'
            task.save()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Задача остановлена пользователем",
                level='warning'
            )
            
            return Response({
                'status': 'success',
                'message': 'Задача успешно остановлена'
            })
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='stop-analysis/(?P<project_id>[^/.]+)')
    def stop_analysis_task(self, request, project_id=None):
        """
        Остановка текущей задачи анализа резюме для проекта
        """
        try:
            # Находим последнюю активную задачу анализа резюме для проекта
            task = self.queryset.filter(
                project_id=project_id, 
                task_type='resume_analysis',
                status='in_progress'
            ).order_by('-created_at').first()
            
            if not task:
                return Response({
                    'status': 'not_found',
                    'message': 'Активная задача анализа резюме не найдена'
                })
            
            # Отмечаем задачу как остановленную
            task.status = 'failed'
            task.error_message = 'Задача остановлена пользователем'
            task.save()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Задача остановлена пользователем",
                level='warning'
            )
            
            return Response({
                'status': 'success',
                'message': 'Задача успешно остановлена'
            })
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='start-analysis/(?P<project_id>[^/.]+)')
    def start_analysis_task(self, request, project_id=None):
        """
        Запуск задачи анализа резюме для проекта
        """
        
        try:
            # Проверяем, есть ли уже активная задача анализа резюме для проекта
            active_task = self.queryset.filter(
                project_id=project_id, 
                task_type='resume_analysis',
                status='in_progress'
            ).exists()
            
            if active_task:
                return Response({
                    'status': 'error',
                    'message': 'Для данного проекта уже запущена задача анализа резюме'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Создаем новую задачу анализа резюме
            serializer = self.get_serializer(data={
                'project': project_id,
                'task_type': 'resume_analysis',
                'status': 'in_progress',
                'progress': 0
            })
            
            serializer.is_valid(raise_exception=True)
            task = serializer.save()
            
            # Создаем запись в логе
            AITaskLog.objects.create(
                task=task,
                message=f"Задача анализа резюме запущена",
                level='info'
            )
            
            # Здесь можно добавить логику для запуска анализа резюме
            # Например, вызов n8n webhook или другой сервис
            
            return Response({
                'status': 'success',
                'message': 'Задача анализа резюме успешно запущена',
                'task_id': task.id
            })
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='create-evaluators/(?P<project_id>[^/.]+)')
    def create_evaluators(self, request, project_id=None):
        try:
            project = Project.objects.get(id=project_id)
            search_criteria = SearchCriteria.objects.filter(project=project).first()
            
            # Подготовка данных для запроса
            payload = {
                'project_id': project.id,
                'must_have': search_criteria.must_have if search_criteria else '',
                'nice_to_have': search_criteria.nice_to_have if search_criteria else '',
                'additional': search_criteria.additional if search_criteria else '',
                'vacancy': project.name,
            }
            
            # Отправка запроса к n8n
            response = requests.post(
                "https://n8n.innoprompt.ru/webhook/9b1bd856-b8a1-4357-b7fc-60cb3d387277",
                json=payload,
            )
            
            # Проверка ответа
            if response.status_code == 200:
                try:
                    data = response.json()
                    prompts = None
                    
                    # Проверяем разные варианты ключей из-за возможной опечатки в API
                    if 'prompts' in data:
                        prompts = data['prompts']
                    elif 'promprts' in data:
                        prompts = data['promprts']
                        
                    if prompts:
                        # Сохранение промптов в поле json_prompts проекта
                        project.json_prompts = prompts
                        project.save()
                        
                        # Обновление статуса проекта
                        project.last_evaluators_update = timezone.now()
                        project.save()
                        
                        return Response({
                            'status': 'success',
                            'message': 'Оценщики успешно созданы',
                            'prompts_count': len(prompts)
                        }, status=status.HTTP_200_OK)
                    else:
                        # Для отладки - логируем полный ответ
                        print(f"Response data from n8n: {data}")
                        return Response({
                            'status': 'error',
                            'message': 'В ответе отсутствуют промпты'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError as ve:
                    print(f"ValueError при обработке ответа: {str(ve)}")
                    return Response({
                        'status': 'error',
                        'message': 'Ошибка при обработке ответа от сервера'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'status': 'error',
                    'message': f'Ошибка при обращении к API: {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Project.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Проект не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Exception в create_evaluators: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Произошла ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)