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
    
    @action(detail=False, methods=['post'], url_path='create-for-project')
    def create_for_project(self, request):
        """
        Создает или обновляет метаданные для указанного проекта.
        """
        print("=== НАЧАЛО ОБРАБОТКИ МЕТАДАННЫХ ПРОЕКТА ===")
        project_id = request.data.get('project')
        print(f"Полученные данные: {request.data}")
        print(f"Комментарий в запросе: {request.data.get('comment')}")
        
        if not project_id:
            return Response(
                {"error": "Project ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Проверяем, существуют ли уже метаданные для этого проекта
        try:
            meta = ProjectMetaData.objects.get(project_id=project_id)
            print(f"Найдены существующие метаданные для проекта {project_id}")
            serializer = self.get_serializer(meta, data=request.data, partial=True)
        except ProjectMetaData.DoesNotExist:
            print(f"Метаданные для проекта {project_id} не найдены, создаем новые")
            serializer = self.get_serializer(data=request.data)
        
        print(f"Данные для сериализатора: {request.data}")
        serializer.is_valid(raise_exception=True)
        print(f"Валидированные данные: {serializer.validated_data}")
        print(f"Комментарий после валидации: {serializer.validated_data.get('comment')}")
        
        instance = serializer.save()
        print(f"Метаданные сохранены. ID: {instance.id}")
        print(f"Сохраненный комментарий: {instance.comment}")
        print("=== КОНЕЦ ОБРАБОТКИ МЕТАДАННЫХ ПРОЕКТА ===")
        
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        
        # Добавляем логирование входящих данных для отладки
        AITaskLog.objects.create(
            task=task,
            message=f"Получены данные от n8n: {request.data}",
            level='info'
        )
        
        # Более безопасное получение result_data
        try:
            result_data = request.data.get('result_data', {})
            # Если result_data пришел как строка (например, JSON-строка), пробуем его распарсить
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            # Если result_data не является словарем, создаем пустой словарь
            if not isinstance(result_data, dict):
                result_data = {}
        except Exception as e:
            error_message = f"Ошибка при обработке result_data: {str(e)}"
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
            )
            result_data = {}
        
        # Отмечаем задачу как завершенную
        task.complete(result_data)
        
        # Создаем запись в логе
        AITaskLog.objects.create(
            task=task,
            message=f"Задача успешно завершена",
            level='success'
        )
        
        # Если это задача генерации поисковых запросов, сохраняем полученные запросы
        try:
            if task.task_type == AITask.TASK_TYPE_SEARCH_QUERY_GENERATION:
                # Проверяем, есть ли search_rows в result_data
                if 'search_rows' in result_data:
                    self.save_search_rows(task.project, result_data['search_rows'])
                # Проверяем, возможно search_rows находится в корне запроса
                elif 'search_rows' in request.data:
                    self.save_search_rows(task.project, request.data['search_rows'])
                # Проверяем ключ с пробелом в конце (ошибка в n8n)
                elif 'search_rows ' in request.data:
                    self.save_search_rows(task.project, request.data['search_rows '])
                else:
                    # Ищем ключ, который может содержать "search_rows" с пробелами или другими вариациями
                    search_rows_key = None
                    for key in request.data.keys():
                        if 'search_rows' in key.lower().strip():
                            search_rows_key = key
                            break
                    
                    if search_rows_key:
                        self.save_search_rows(task.project, request.data[search_rows_key])
                        AITaskLog.objects.create(
                            task=task,
                            message=f"Найдены данные search_rows в ключе '{search_rows_key}'",
                            level='info'
                        )
                    else:
                        AITaskLog.objects.create(
                            task=task,
                            message="Не найдены данные search_rows в запросе",
                            level='warning'
                        )
        except Exception as e:
            error_message = f"Ошибка при сохранении поисковых запросов: {str(e)}"
            AITaskLog.objects.create(
                task=task,
                message=error_message,
                level='error'
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
    
    def save_search_rows(self, project, search_rows_data):
        """
        Сохраняет поисковые запросы, полученные от n8n.
        """
        # Удаляем существующие поисковые запросы
        project.search_rows.all().delete()
        
        # Создаем новые поисковые запросы
        for row_data in search_rows_data:
            SearchRow.objects.create(
                project=project,
                text=row_data.get('text', ''),
                logic=row_data.get('logic', 'any'),
                period=row_data.get('period', 'all_time'),
                field=row_data.get('field', 'everywhere')
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