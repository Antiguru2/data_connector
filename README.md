# data_connector
Инструмент для обмена данными между django проектами.

### ОПИСАНИЕ:

Data Connector - это специализированное Django-приложение, разработанное для обеспечения надежного и гибкого обмена данными между различными Django-проектами. 

#### Основные возможности:

- **Двусторонняя синхронизация данных** между разными Django-проектами
- **Гибкая настройка сериализации** данных для каждого типа модели
- **Автоматическая обработка связей** между моделями (ForeignKey, ManyToMany)
- **Поддержка различных типов данных** и их преобразование
- **Мониторинг и логирование** всех операций обмена данными
- **Безопасная передача данных** с поддержкой аутентификации
- **Обработка ошибок** и автоматические повторные попытки при сбоях

#### Типичные сценарии использования:

1. **Распределенные системы** - когда данные должны быть синхронизированы между несколькими независимыми Django-приложениями
2. **Микросервисная архитектура** - для обмена данными между микросервисами на базе Django
3. **Резервное копирование** - для создания резервных копий данных в отдельном проекте
4. **Агрегация данных** - для сбора и объединения данных из разных источников
5. **Тестовые окружения** - для синхронизации данных между продакшн и тестовыми средами

### СОЗДАНИЕ CRUD ОПЕРАЦИЙ:

#### 1. Создание сериализатора

1. Создайте файл сериализатора в директории `export_serializers/` или `import_serializers/` в зависимости от типа операции:

```python
from rest_framework import serializers
from your_app.models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = [
            'id',
            'field1',
            'field2',
            # ... другие поля
        ]
        read_only_fields = ['id', 'created_at']  # поля только для чтения
```

#### 2. Создание ViewSet

1. Создайте или дополните файл `local_api.py`:

```python
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from .export_serializers import YourModelSerializer
from your_app.models import YourModel

class YourModelViewSet(ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsStaffPermission,  # или другие классы разрешений
    ]

    def list(self, request, *args, **kwargs):
        # Кастомная логика для GET запросов
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # Кастомная логика для POST запросов
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

#### 3. Регистрация маршрутов

1. Добавьте маршрут в `local_router.py`:

```python
from rest_framework import routers
from . import local_api

router = routers.DefaultRouter()
router.register(r'your-model', local_api.YourModelViewSet)
```

#### 4. Настройка прав доступа

1. Создайте классы разрешений при необходимости:

```python
class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Ваша логика проверки прав
        return True
```

#### 5. Использование API

После настройки API будет доступно по следующим эндпоинтам:

- `GET /data_connector/api/your-model/` - получение списка объектов
- `POST /data_connector/api/your-model/` - создание нового объекта
- `GET /data_connector/api/your-model/{id}/` - получение конкретного объекта
- `PUT /data_connector/api/your-model/{id}/` - обновление объекта
- `DELETE /data_connector/api/your-model/{id}/` - удаление объекта

#### Пример использования:

```python
# Создание объекта
response = requests.post('http://your-api/data_connector/api/your-model/', json={
    'field1': 'value1',
    'field2': 'value2'
})

# Получение объекта
response = requests.get('http://your-api/data_connector/api/your-model/1/')

# Обновление объекта
response = requests.put('http://your-api/data_connector/api/your-model/1/', json={
    'field1': 'new_value'
})

# Удаление объекта
response = requests.delete('http://your-api/data_connector/api/your-model/1/')
```

### АРХИТЕКТУРА:

![карта моделей](project_models.png)

#### Основные компоненты:

1. **Модели данных** (`models.py`):
   - `DataConnector` - основная модель для настройки сериализации данных
   - `FieldHandler` - обработчик полей для сериализации
   - `SerializerField` - поле сериализатора с различными типами данных
   - `RemoteSite` - модель для хранения информации о удалённых сайтах
   - `Transmitter` - модель для передачи данных между проектами
   - `TransmitterLog` - логирование операций передачи данных

2. **API и Роутинг**:
   - `local_api.py` - содержит ViewSet'ы для REST API
   - `local_router.py` - настройка маршрутизации REST API
   - Поддерживает CRUD операции для всех основных моделей
   - Включает кастомные эндпоинты для специфических операций

3. **Сериализация**:
   - Директория `export_serializers/` - сериализаторы для экспорта данных
   - Директория `import_serializers/` - сериализаторы для импорта данных
   - Гибкая система обработки полей через `FieldHandler`

4. **Безопасность**:
   - Встроенная система разрешений
   - Поддержка аутентификации
   - Контроль доступа на уровне моделей и API

5. **Дополнительные возможности**:
   - Поддержка пагинации
   - Фильтрация данных
   - Логирование операций
   - Гибкая настройка прав доступа

### Использование:

1. Настройка удалённого сайта через модель `RemoteSite`
2. Создание конфигурации сериализации через `DataConnector`
3. Настройка передатчиков через модель `Transmitter`
4. Мониторинг операций через `TransmitterLog`

Изменения
добавлен файл local_router
он для подключения рест роутеров

### Сериализаторы для расширенных данных кандидатов

#### CandidateImportSerializer
```python
class CandidateImportSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='resume_title')
    name = serializers.CharField(source='candidat_full_name')
    experience = serializers.CharField(source='experience_text')
    ai_comment = serializers.CharField(source='comment')
    resume_url = serializers.CharField(source='hh_url')
    
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
        ]
```

#### Расширенные поля в сериализаторах
- `experience_text`: Текстовое представление опыта работы
- `experience_json`: Структурированное представление опыта в JSON
- `total_experience_years`: Общий опыт работы в годах
- `salary`: Зарплатные ожидания кандидата
- `age`: Возраст кандидата
- `gender`: Пол кандидата
- `area`: Регион/город кандидата
- `contact_email`: Email для связи
- `contact_phone`: Телефон для связи
- `resume_updated_at`: Дата последнего обновления резюме