import os
import json
import traceback

from tqdm import tqdm
from datetime import datetime

from django.db import models
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.management.base import BaseCommand, CommandError

from data_connector.models import DataConnector

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает дамп данных с использованием DataConnector'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Название приложения для создания дампа (по умолчанию: data_connector)',
            default='data_connector'
        )
        parser.add_argument(
            '--output_file_path',
            type=str,
            help='Полный путь к файлу для сохранения дампа (по умолчанию: auto-generated в BASE_DIR/fixtures/dumps/)',
        )
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='Список моделей для включения в дамп (по умолчанию: все модели приложения)',
        )
        parser.add_argument(
            '--exclude',
            nargs='+',
            type=str,
            help='Список моделей для исключения из дампа',
        )

    def handle(self, *args, **options):
        app_name = options['app']
        output_file_path = options['output_file_path']
        include_models = options['models']
        exclude_models = options['exclude'] or []

        try:
            output_path = create_dump(
                app_name=app_name,
                output_file_path=output_file_path,
                include_models=include_models,
                exclude_models=exclude_models,
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Дамп успешно создан! Файл: {output_path}'
                )
            )
            
        except Exception as e:
            traceback.print_exc()
            raise CommandError(f'Ошибка при создании дампа: {str(e)}')
    

def create_dump(
    app_name='data_connector', 
    output_file_path=None, 
    include_models=None, 
    exclude_models=None,
):
    """
    Создает дамп данных для локальной разработки с использованием DataConnector
    
    Args:
        app_name (str): Название приложения для создания дампа
        output_file_path (str): Полный путь к файлу для сохранения дампа
        include_models (list): Список моделей для включения в дамп
        exclude_models (list): Список моделей для исключения из дампа
    
    Returns:
        str: Путь к созданному файлу дампа
    
    Raises:
        CommandError: При ошибках в процессе создания дампа
    """
    # Получаем все модели приложения
    try:
        app_config = apps.get_app_config(app_name)
        app_models = list(app_config.get_models())  # Преобразуем генератор в список
    except LookupError:
        raise CommandError(f'Приложение "{app_name}" не найдено')

    # Фильтруем модели
    if include_models:
        app_models = [model for model in app_models if model._meta.model_name in include_models]
    
    if exclude_models:
        app_models = [model for model in app_models if model._meta.model_name not in exclude_models]

    # Определяем путь к файлу
    if output_file_path:
        # Создаем директорию если она не существует
        output_dir = os.path.dirname(output_file_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    else:
        # Генерируем имя файла и путь по умолчанию
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{app_name}_dump_{timestamp}.json"
        fixtures_dir = os.path.join(settings.BASE_DIR, 'fixtures', 'dumps')
        os.makedirs(fixtures_dir, exist_ok=True)
        output_file_path = os.path.join(fixtures_dir, filename)

    print(f'Создание дампа для приложения "{app_name}"...')
    print(f'Модели: {[model._meta.model_name for model in app_models]}')
    print(f'Файл: {output_file_path}')

    # Получаем или создаем пользователя для сериализатора
    try:
        super_user = User.objects.filter(is_superuser=True).first()
        if not super_user:
            # Создаем временного пользователя если нет никого
            super_user = User.objects.create(
                username='dump_user',
                is_superuser=True,
                is_staff=True
            )
    except Exception as e:
        print(f'Предупреждение: Не удалось получить пользователя: {e}')
        super_user = None

    # Собираем данные
    dump_data = {}
    
    # Основной прогресс-бар для моделей
    for model in tqdm(app_models, desc="Обработка моделей", unit="модель"):
        model_name = model._meta.model_name
        tqdm.write(f"Обработка модели: {model_name}")
        
        # Получаем все объекты модели
        queryset = model.objects.all()
        
        if queryset.exists():
            # Получаем или создаем DataConnector для модели
            super_user = User.objects.filter(is_superuser=True).first()
            serializer = DataConnector.get_serializer(
                some_model=model,
                user=super_user,
            )
            
            # Сериализуем данные через DataConnector
            model_data = serializer.get_data(queryset, diving_depth='max')
            
            # Сохраняем данные модели под ключом natural_key
            natural_key = f"{app_name}.{model_name}"
            dump_data[natural_key] = model_data
            
            record_count = len(model_data) if isinstance(model_data, list) else 1
            tqdm.write(f"  ✓ Добавлено {record_count} записей для модели {model_name}")
        else:
            tqdm.write(f"  ⚠ Модель {model_name} не содержит данных")

    print('dump_data', dump_data)
    # Сохраняем дамп
    total_records = sum(
        len(data) if isinstance(data, list) else 1 
        for data in dump_data.values()
    )
    
    tqdm.write(f'Сохранение дампа в файл...')
    tqdm.write(f'Всего моделей: {len(dump_data)}')
    tqdm.write(f'Всего записей: {total_records}')
    
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(dump_data, f, ensure_ascii=False, indent=2)

    print(f'Дамп успешно создан! Обработано {len(dump_data)} моделей, {total_records} записей.')
    print(f'Файл: {output_file_path}')

    return output_file_path
