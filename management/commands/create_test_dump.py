from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from data_connector.models import (
    MainTestModel,
    OneToOneModel,
    ForInKeyModel,
    ManyToManyModel,
    GenericRelatedModel,
    DataConnector,
    SerializerField,
    RemoteSite,
    Transmitter,
    TransmitterLog,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает тестовые данные и дамп для проверки системы дампов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Название файла для сохранения дампа (по умолчанию: test_dump.json)',
            default='test_dump.json'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        self.stdout.write('Создание тестовых данных...')
        
        # Создаем пользователей
        user1 = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )
        
        user2 = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@example.com'
        )

        # Создаем тестовые модели
        one_to_one_model = OneToOneModel.objects.create(
            char_field='Тестовое значение OneToOne',
            integer_field=42,
            float_field=3.14,
            boolean_field=True,
            text_field='Длинный текст для OneToOne модели'
        )
        
        for_in_key_model = ForInKeyModel.objects.create(
            char_field='Тестовое значение ForeignKey',
            integer_field=100,
            float_field=2.71,
            boolean_field=False,
            text_field='Длинный текст для ForeignKey модели'
        )

        # Создаем ManyToMany модели
        manytomany_models = []
        for i in range(3):
            manytomany_model = ManyToManyModel.objects.create(
                char_field=f'ManyToMany модель {i+1}',
                integer_field=i * 10,
                float_field=i * 1.5,
                boolean_field=i % 2 == 0,
                text_field=f'Текст для ManyToMany модели {i+1}'
            )
            manytomany_models.append(manytomany_model)

        # Создаем основную модель
        main_model = MainTestModel.objects.create(
            one_to_one_model=one_to_one_model,
            for_in_key_model=for_in_key_model,
            char_field='Основная тестовая модель',
            integer_field=999,
            float_field=9.99,
            boolean_field=True,
            text_field='Основной текст для тестирования'
        )
        
        # Устанавливаем ManyToMany связи
        main_model.many_to_many_models.set(manytomany_models)

        # Создаем GenericRelated модель
        generic_model = GenericRelatedModel.objects.create(
            content_type=ContentType.objects.get_for_model(main_model),
            object_id=main_model.id,
            char_field='Generic Related модель',
            integer_field=777,
            float_field=7.77,
            boolean_field=True,
            text_field='Текст для Generic Related модели'
        )

        # Создаем DataConnector и SerializerField
        content_type = ContentType.objects.get_for_model(MainTestModel)
        data_connector = DataConnector.objects.create(
            name='Тестовый сериализатор',
            slug='test-serializer',
            description='Сериализатор для тестирования',
            content_type=content_type,
            is_active=True,
            is_allow_view=True,
            is_allow_edit=True,
            is_allow_delete=False,
            is_allow_create=True
        )

        # Создаем поля сериализатора
        SerializerField.objects.create(
            name='char_field',
            verbose_name='Текстовое поле',
            type='CharField',
            data_connector=data_connector,
            is_active=True,
            order=1
        )
        
        SerializerField.objects.create(
            name='integer_field',
            verbose_name='Целое число',
            type='IntegerField',
            data_connector=data_connector,
            is_active=True,
            order=2
        )
        
        SerializerField.objects.create(
            name='one_to_one_model',
            verbose_name='OneToOne связь',
            type='OneToOneField',
            data_connector=data_connector,
            is_active=True,
            order=3
        )

        # Создаем RemoteSite
        remote_site = RemoteSite.objects.create(
            name='Тестовый удаленный сайт',
            domain='test.example.com'
        )

        # Создаем Transmitter
        transmitter = Transmitter.objects.create(
            name='Тестовый передатчик',
            action='send',
            mod='test',
            data_connector=data_connector,
            model_id=main_model.id,
            remote_site=remote_site,
            run_on_save=True
        )

        # Создаем TransmitterLog
        TransmitterLog.objects.create(
            transmitter=transmitter,
            status='success',
            result={'message': 'Тестовый успешный результат'}
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Тестовые данные созданы! Теперь можно создать дамп командой:\n'
                f'python manage.py create_dump --output {output_file}'
            )
        ) 