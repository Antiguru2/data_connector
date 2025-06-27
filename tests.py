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

        main_model_natural_key = f"{self.main_model._meta.app_label}.{self.main_model._meta.model_name}"
        self.default_api_url = f"https://127.0.0.1:8000/data_connector/super-api/{main_model_natural_key}/"

    def get_key_form_format_value(self, data: dict, key: str):
        key_form_format_value = None
        field_data = data.get(key)
        if field_data:
            key_form_format_value = field_data.get('value')
        return key_form_format_value

    def test_api_key_form_format(self):
        # print("test_api_get_key_form_format")
        """
        Тест получения данных в формате key-form
        """
        key_form_url = self.default_api_url + f"{self.main_model.id}/" + "key-form/"
        # response = self.client.get(key_form_url)
        # self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)
        response = self.client.get(key_form_url)
        if response.status_code != 200:
            try:
                print('error', response.json())
            except Exception as e:
                print('error', response.content)

        self.assertEqual(response.status_code, 200)
        data = response.json().get('data')[0]


        self.assertEqual(self.get_key_form_format_value(data, 'id'), self.main_model.id)
        self.assertEqual(self.get_key_form_format_value(data, 'char_field'), self.main_model.char_field)
        self.assertEqual(self.get_key_form_format_value(data, 'integer_field'), self.main_model.integer_field)
        self.assertEqual(self.get_key_form_format_value(data, 'float_field'), self.main_model.float_field)
        self.assertEqual(self.get_key_form_format_value(data, 'boolean_field'), self.main_model.boolean_field)
        self.assertIsInstance(self.get_key_form_format_value(data, 'datetime_field'), str)
        self.assertEqual(self.get_key_form_format_value(data, 'text_field'), self.main_model.text_field)

        self.assertEqual(self.get_key_form_format_value(data, 'one_to_one_model'), self.main_model.one_to_one_model.id)
        self.assertEqual(self.get_key_form_format_value(data, 'for_in_key_model'), self.main_model.for_in_key_model.id)
        self.assertEqual(self.get_key_form_format_value(data, 'many_to_many_models'), [model.id for model in self.main_model.many_to_many_models.all()])

