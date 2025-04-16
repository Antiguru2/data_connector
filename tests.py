from datetime import datetime

from django.test import TestCase
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from data_connector.models import (
    MainTestModel,
    OneToOneModel,
    ForInKeyModel,
    ManyToManyModel,
    GenericRelatedModel,
)

User = get_user_model()


class DataConnectorTestCase(TestCase):
    """
    Базовый класс для тестирования data_connector.
    Запускает менеджмент команду для создания тестовых данных.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Создает тестовые данные для всех тестов.
        """
        from django.core.management import call_command
        call_command('create_test_data')

    def setUp(self):
        """
        Подготовка данных для каждого теста.
        """
        self.user = User.objects.get(username='testuser')
        self.superuser = User.objects.get(username='admin')

        self.main_model = MainTestModel.objects.first()
        self.one_to_one_model = OneToOneModel.objects.first()
        self.forinkey_model = ForInKeyModel.objects.first()
        self.manytomany_models = ManyToManyModel.objects.all()
        self.generic_model = GenericRelatedModel.objects.first()

        self.dict_api_url = f"https://127.0.0.1:8000/data_connector/super-api/{self.main_model._meta.app_label}.{self.main_model._meta.model_name}/"
        self.list_api_url = f"https://127.0.0.1:8000/data_connector/super-api/form/{self.main_model._meta.app_label}.{self.main_model._meta.model_name}/"

    def test_api_get_dict_format(self):
        print("test_api_get_dict_format")
        """
        Тест получения данных в формате dict.
        """
        response = self.client.get(self.dict_api_url + f"{self.main_model.id}/")
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)
        response = self.client.get(self.dict_api_url + f"{self.main_model.id}/")
        # print('response')
        # try:
        #     print(response.json())
        # except:
        #     print(response.content)

        self.assertEqual(response.status_code, 200)
        data = response.json().get('data')[0]


        self.assertEqual(data.get('id'), self.main_model.id)
        self.assertEqual(data.get('char_field'), self.main_model.char_field)
        self.assertEqual(data.get('integer_field'), self.main_model.integer_field)
        self.assertEqual(data.get('float_field'), self.main_model.float_field)
        self.assertEqual(data.get('boolean_field'), self.main_model.boolean_field)
        self.assertIsInstance(data.get('datetime_field'), str)
        self.assertEqual(data.get('text_field'), self.main_model.text_field)

        self.assertEqual(data.get('one_to_one_model'), self.main_model.one_to_one_model.id)
        self.assertEqual(data.get('for_in_key_model'), self.main_model.for_in_key_model.id)
        self.assertEqual(data.get('many_to_many_models'), [model.id for model in self.main_model.many_to_many_models.all()])

    def test_api_list_dict_format(self):
        print("test_api_get_list_format")

        response = self.client.get(self.dict_api_url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)
        response = self.client.get(self.dict_api_url)
        # print('response')
        # try:
        #     print(response.json())
        # except:
        #     print(response.content)

        self.assertEqual(response.status_code, 200)
        data = response.json().get('data')
        self.assertEqual(len(data), 2)
        
    def test_api_get_list_format(self):
        print("test_api_get_list_format")
        """
        Тест получения данных в формате list.
        """
        response = self.client.get(self.list_api_url + f"{self.main_model.id}/")
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)
        response = self.client.get(self.list_api_url + f"{self.main_model.id}/")
        # print('response')
        # try:
        #     print(response.json())
        # except:
        #     print(response.content)

        data = response.json().get('data')
        default_fields = ['id', 'char_field', 'integer_field', 'float_field', 'boolean_field', 'text_field']
        for field in data:
            if field.get('name') in default_fields:
                self.assertEqual(field.get('value'), getattr(self.main_model, field.get('name')))

            elif field.get('name') == 'one_to_one_model':
                self.assertEqual(field.get('value'), self.main_model.one_to_one_model.id)

            elif field.get('name') == 'for_in_key_model':
                self.assertEqual(field.get('value'), self.main_model.for_in_key_model.id)

            elif field.get('name') == 'many_to_many_models':
                self.assertEqual(field.get('value'), [model.id for model in self.main_model.many_to_many_models.all()])

            else:
                ...
                
                
                
            



    # def test_api_get_list_format(self):
    #     """
    #     Тест получения данных в формате list.
    #     """
    #     response = self.client.get(self.api_url, {'format': 'list'})
    #     self.assertEqual(response.status_code, 200)
    #     data = response.json()
    #     self.assertIsInstance(data, list)
    #     for field in data:
    #         self.assertIn('name', field)
    #         self.assertIn('value', field)
    #         self.assertIn('verbose_name', field)

    # def test_api_post_dict_format(self):
    #     """
    #     Тест создания данных в формате dict.
    #     """
    #     data = {
    #         'name': 'Новая тестовая модель',
    #         'description': 'Описание новой модели',
    #         'is_active': True,
    #     }
    #     response = self.client.post(self.api_url, data, content_type='application/json')
    #     self.assertEqual(response.status_code, 201)
    #     self.assertTrue(__MainTestModel.objects.filter(name='Новая тестовая модель').exists())

    # def test_api_post_list_format(self):
    #     """
    #     Тест создания данных в формате list.
    #     """
    #     data = [
    #         {
    #             'name': 'name',
    #             'value': 'Новая тестовая модель',
    #             'verbose_name': 'Название',
    #         },
    #         {
    #             'name': 'description',
    #             'value': 'Описание новой модели',
    #             'verbose_name': 'Описание',
    #         },
    #         {
    #             'name': 'is_active',
    #             'value': True,
    #             'verbose_name': 'Активен',
    #         },
    #     ]
    #     response = self.client.post(self.api_url, data, content_type='application/json')
    #     self.assertEqual(response.status_code, 201)
    #     self.assertTrue(__MainTestModel.objects.filter(name='Новая тестовая модель').exists())
