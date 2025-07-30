"""
Пример использования системы дампов Data Connector

Этот файл демонстрирует различные способы использования команды create_dump
для создания и загрузки дампов данных с использованием DataConnector.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Примеры использования системы дампов Data Connector'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Запустить демонстрацию всех возможностей'
        )

    def handle(self, *args, **options):
        if options['demo']:
            self.run_demo()
        else:
            self.show_examples()

    def run_demo(self):
        """Запускает полную демонстрацию системы дампов"""
        self.stdout.write(
            self.style.SUCCESS('🚀 Демонстрация системы дампов Data Connector\n')
        )

        # Создаем директорию для демо
        demo_dir = os.path.join(settings.BASE_DIR, 'fixtures', 'demo')
        os.makedirs(demo_dir, exist_ok=True)

        # 1. Создание базового дампа в REST формате
        self.stdout.write('📦 1. Создание базового дампа в REST формате...')
        try:
            call_command(
                'create_dump', 'create',
                app='data_connector',
                data_type='rest',
                output_file_path=os.path.join(demo_dir, 'basic_rest_dump.json')
            )
            self.stdout.write(self.style.SUCCESS('✅ Базовый REST дамп создан'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

        # 2. Создание дампа в FORM формате
        self.stdout.write('📋 2. Создание дампа в FORM формате...')
        try:
            call_command(
                'create_dump', 'create',
                app='data_connector',
                data_type='form',
                output_file_path=os.path.join(demo_dir, 'form_dump.json')
            )
            self.stdout.write(self.style.SUCCESS('✅ FORM дамп создан'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

        # 3. Создание дампа с метаданными
        self.stdout.write('🔧 3. Создание дампа с метаданными DataConnector...')
        try:
            call_command(
                'create_dump', 'create',
                app='data_connector',
                data_type='rest',
                include_data_connector=True,
                include_serializer_fields=True,
                output_file_path=os.path.join(demo_dir, 'full_dump.json')
            )
            self.stdout.write(self.style.SUCCESS('✅ Полный дамп с метаданными создан'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

        # 4. Создание дампа только тестовых моделей
        self.stdout.write('🧪 4. Создание дампа только тестовых моделей...')
        try:
            call_command(
                'create_dump', 'create',
                app='data_connector',
                models=['MainTestModel', 'OneToOneModel', 'ForInKeyModel'],
                data_type='key-form',
                output_file_path=os.path.join(demo_dir, 'test_models_dump.json')
            )
            self.stdout.write(self.style.SUCCESS('✅ Дамп тестовых моделей создан'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

        # 5. Создание дампа с исключением определенных моделей
        self.stdout.write('🚫 5. Создание дампа с исключением логов...')
        try:
            call_command(
                'create_dump', 'create',
                app='data_connector',
                exclude=['TransmitterLog'],
                data_type='rest',
                output_file_path=os.path.join(demo_dir, 'clean_dump.json')
            )
            self.stdout.write(self.style.SUCCESS('✅ Чистый дамп создан'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

        self.stdout.write('\n🎉 Демонстрация завершена!')
        self.stdout.write(f'📁 Файлы дампов сохранены в: {demo_dir}')
        self.show_demo_files(demo_dir)

    def show_demo_files(self, demo_dir):
        """Показывает созданные файлы дампов"""
        self.stdout.write('\n📄 Созданные файлы дампов:')
        if os.path.exists(demo_dir):
            for filename in os.listdir(demo_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(demo_dir, filename)
                    file_size = os.path.getsize(file_path)
                    self.stdout.write(f'  📄 {filename} ({file_size} байт)')

    def show_examples(self):
        """Показывает примеры использования команды"""
        self.stdout.write(
            self.style.SUCCESS('📚 Примеры использования системы дампов Data Connector\n')
        )

        examples = [
            {
                'title': 'Базовое создание дампа',
                'description': 'Создать дамп всех моделей приложения в REST формате',
                'command': 'python manage.py create_dump create --app data_connector'
            },
            {
                'title': 'Создание дампа в FORM формате',
                'description': 'Создать дамп в формате FORM для работы с формами',
                'command': 'python manage.py create_dump create --app data_connector --data_type form'
            },
            {
                'title': 'Создание дампа с метаданными',
                'description': 'Включить в дамп информацию о DataConnector и SerializerField',
                'command': 'python manage.py create_dump create --app data_connector --include_data_connector --include_serializer_fields'
            },
            {
                'title': 'Фильтрация моделей',
                'description': 'Создать дамп только определенных моделей',
                'command': 'python manage.py create_dump create --app data_connector --models MainTestModel OneToOneModel'
            },
            {
                'title': 'Исключение моделей',
                'description': 'Создать дамп с исключением определенных моделей',
                'command': 'python manage.py create_dump create --app data_connector --exclude TransmitterLog'
            },
            {
                'title': 'Кастомный путь к файлу',
                'description': 'Указать конкретный путь для сохранения дампа',
                'command': 'python manage.py create_dump create --app data_connector --output_file_path /path/to/my_dump.json'
            },
            {
                'title': 'Загрузка дампа',
                'description': 'Загрузить данные из созданного дампа',
                'command': 'python manage.py create_dump load --input_file_path /path/to/dump.json'
            },
            {
                'title': 'Загрузка с очисткой',
                'description': 'Очистить существующие данные перед загрузкой дампа',
                'command': 'python manage.py create_dump load --input_file_path /path/to/dump.json --clear_existing'
            },
            {
                'title': 'Демонстрация всех возможностей',
                'description': 'Запустить полную демонстрацию системы',
                'command': 'python manage.py example_dump_usage --demo'
            }
        ]

        for i, example in enumerate(examples, 1):
            self.stdout.write(f'\n{i}. {example["title"]}')
            self.stdout.write(f'   {example["description"]}')
            self.stdout.write(f'   💻 {example["command"]}')

        self.stdout.write('\n' + '='*60)
        self.stdout.write('💡 Советы по использованию:')
        self.stdout.write('   • Используйте --data_type для выбора формата данных')
        self.stdout.write('   • Добавьте --include_data_connector для сохранения настроек сериализаторов')
        self.stdout.write('   • Используйте --clear_existing при загрузке на чистую среду')
        self.stdout.write('   • Фильтруйте модели для создания частичных дампов')
        self.stdout.write('   • Проверяйте размеры файлов для больших дампов')

        self.stdout.write('\n📖 Подробная документация:')
        self.stdout.write('   📄 DUMP_SYSTEM_SUMMARY.md - Полное описание системы')
        self.stdout.write('   📄 README.md - Общая документация приложения') 