from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from data_connector.models import (
    MainTestModel,
    OneToOneModel,
    ForInKeyModel,
    ManyToManyModel,
    GenericRelatedModel,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает тестовые данные для моделей data_connector'

    def handle(self, *args, **options):
        self.stdout.write('Создание пользователя...')
        User.objects.create_user(
            username='testuser',
            password='testpassword',
        )
        User.objects.create_superuser(
            username='admin',
            password='admin',
        )

        self.stdout.write('Создание тестовых данных...')

        one_to_one_model = OneToOneModel.objects.create()
        for_in_key_model = ForInKeyModel.objects.create()

        main_model = MainTestModel.objects.create(
            one_to_one_model=one_to_one_model,
            for_in_key_model=for_in_key_model,
        )
        main_model = MainTestModel.objects.create()
        
        manytomany_models = []
        for i in range(10):
            manytomany_models.append(ManyToManyModel.objects.create())

        main_model.many_to_many_models.set(manytomany_models)

        generic_model = GenericRelatedModel.objects.create(
            content_type=ContentType.objects.get_for_model(main_model),
            object_id=main_model.id,
        )

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!')) 