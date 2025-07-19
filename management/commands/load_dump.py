import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.apps import apps


class Command(BaseCommand):
    help = 'Загружает дамп данных для локальной разработки с учетом generic relations'

    def add_arguments(self, parser):
        parser.add_argument(
            'dump_file',
            type=str,
            help='Путь к файлу дампа для загрузки'
        )
        parser.add_argument(
            '--app',
            type=str,
            help='Название приложения (по умолчанию: data_connector)',
            default='data_connector'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед загрузкой',
        )
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='Список моделей для загрузки (по умолчанию: все модели из дампа)',
        )

    def handle(self, *args, **options):
        dump_file = options['dump_file']
        app_name = options['app']
        clear_data = options['clear']
        include_models = options['models']

        # Проверяем существование файла
        if not os.path.exists(dump_file):
            # Пробуем найти файл в fixtures директории
            app_config = apps.get_app_config(app_name)
            fixtures_path = os.path.join(app_config.path, 'fixtures', dump_file)
            if os.path.exists(fixtures_path):
                dump_file = fixtures_path
            else:
                raise CommandError(f'Файл дампа не найден: {dump_file}')

        self.stdout.write(f'Загрузка дампа из файла: {dump_file}')

        # Загружаем данные из файла
        try:
            with open(dump_file, 'r', encoding='utf-8') as f:
                dump_data = json.load(f)
        except Exception as e:
            raise CommandError(f'Ошибка при чтении файла дампа: {str(e)}')

        # Фильтруем данные по моделям если указано
        if include_models:
            dump_data = [
                item for item in dump_data 
                if any(model in item['model'] for model in include_models)
            ]

        # Группируем данные по моделям
        models_data = {}
        for item in dump_data:
            model_name = item['model']
            if model_name not in models_data:
                models_data[model_name] = []
            models_data[model_name].append(item)

        # Очищаем данные если требуется
        if clear_data:
            self.stdout.write('Очистка существующих данных...')
            self.clear_existing_data(models_data.keys())

        # Загружаем данные в правильном порядке
        self.stdout.write('Загрузка данных...')
        
        with transaction.atomic():
            # Первый проход: создаем объекты без связей
            created_objects = {}
            
            for model_name, items in models_data.items():
                self.stdout.write(f'Обработка модели: {model_name}')
                
                for item in items:
                    obj = self.create_object_without_relations(item)
                    if obj:
                        created_objects[f"{model_name}:{item['pk']}"] = obj

            # Второй проход: устанавливаем связи
            for model_name, items in models_data.items():
                for item in items:
                    self.setup_relations(item, created_objects)

        self.stdout.write(
            self.style.SUCCESS(
                f'Дамп успешно загружен! Обработано {len(dump_data)} объектов.'
            )
        )

    def clear_existing_data(self, model_names):
        """
        Очищает существующие данные для указанных моделей
        """
        for model_name in model_names:
            try:
                app_label, model_name_short = model_name.split('.')
                model = apps.get_model(app_label, model_name_short)
                count = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'Удалено {count} объектов модели {model_name}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Ошибка при очистке модели {model_name}: {str(e)}'
                    )
                )

    def create_object_without_relations(self, item):
        """
        Создает объект без установки связей
        """
        try:
            model_name = item['model']
            pk = item['pk']
            fields = item['fields']

            # Получаем модель
            app_label, model_name_short = model_name.split('.')
            model = apps.get_model(app_label, model_name_short)

            # Подготавливаем поля для создания объекта
            create_fields = {}
            
            for field_name, field_value in fields.items():
                # Пропускаем поля, которые будут обработаны отдельно
                if field_name.endswith('_related'):
                    continue
                
                field = model._meta.get_field(field_name)
                
                # Обрабатываем различные типы полей
                if isinstance(field, models.ForeignKey):
                    # ForeignKey будет установлен во втором проходе
                    continue
                
                elif isinstance(field, models.ManyToManyField):
                    # ManyToManyField будет установлен во втором проходе
                    continue
                
                elif isinstance(field, models.DateTimeField):
                    # Преобразуем строку обратно в datetime
                    if field_value:
                        from django.utils.dateparse import parse_datetime
                        create_fields[field_name] = parse_datetime(field_value)
                    else:
                        create_fields[field_name] = None
                
                elif isinstance(field, models.DateField):
                    # Преобразуем строку обратно в date
                    if field_value:
                        from datetime import datetime
                        create_fields[field_name] = datetime.fromisoformat(field_value).date()
                    else:
                        create_fields[field_name] = None
                
                else:
                    # Для остальных полей сохраняем как есть
                    create_fields[field_name] = field_value

            # Создаем объект
            obj = model.objects.create(**create_fields)
            
            # Если PK был указан в дампе, устанавливаем его
            if pk is not None:
                obj.pk = pk
                obj.save(update_fields=['pk'])
            
            return obj
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'Ошибка при создании объекта {item["model"]}:{item["pk"]}: {str(e)}'
                )
            )
            return None

    def setup_relations(self, item, created_objects):
        """
        Устанавливает связи для созданного объекта
        """
        try:
            model_name = item['model']
            pk = item['pk']
            fields = item['fields']

            # Получаем модель и объект
            app_label, model_name_short = model_name.split('.')
            model = apps.get_model(app_label, model_name_short)
            
            obj_key = f"{model_name}:{pk}"
            if obj_key not in created_objects:
                return
            
            obj = created_objects[obj_key]

            # Устанавливаем ForeignKey связи
            for field_name, field_value in fields.items():
                if field_name.endswith('_related'):
                    continue
                
                try:
                    field = model._meta.get_field(field_name)
                except:
                    continue

                if isinstance(field, models.ForeignKey):
                    if field_value is not None:
                        # Находим связанный объект
                        related_obj = self.find_related_object(field.related_model, field_value, created_objects)
                        if related_obj:
                            setattr(obj, field_name, related_obj)
                
                elif isinstance(field, models.ManyToManyField):
                    if field_value and isinstance(field_value, list):
                        # Находим связанные объекты
                        related_objects = []
                        for related_pk in field_value:
                            related_obj = self.find_related_object(field.related_model, related_pk, created_objects)
                            if related_obj:
                                related_objects.append(related_obj)
                        
                        # Устанавливаем ManyToMany связь
                        getattr(obj, field_name).set(related_objects)

            # Сохраняем объект
            obj.save()
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'Ошибка при установке связей для {item["model"]}:{item["pk"]}: {str(e)}'
                )
            )

    def find_related_object(self, related_model, pk, created_objects):
        """
        Находит связанный объект среди созданных объектов
        """
        model_key = f"{related_model._meta.app_label}.{related_model._meta.model_name}:{pk}"
        
        if model_key in created_objects:
            return created_objects[model_key]
        
        # Если объект не найден среди созданных, пробуем найти в базе данных
        try:
            return related_model.objects.get(pk=pk)
        except:
            return None 