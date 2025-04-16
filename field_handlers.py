from django.db import models
from django.contrib.contenttypes.models import ContentType


class Handler():
    """
        Класс, инструкция для обработки поля.
    """
    def __init__(self, name: str):
        self.name = name


class FieldHandler(Handler):
    """
        Класс, инструкция для обработки поля.
    """

    def get_value(self, obj, serializer_field: models.Model):
        serializer_field_name = serializer_field.name
        value = 'Не найдено'

        if isinstance(obj, models.Model):
            obj: models.Model
            if hasattr(obj, serializer_field_name):
                try:
                    value = getattr(obj, serializer_field_name)
                    print('value', value)
                except Exception as e:
                    print(e)
                    value = f'Ошибка: {e}'

        elif isinstance(obj, dict):
            obj: dict
            if serializer_field_name in obj.keys():
                try:
                    value = obj.get(serializer_field_name)
                    # print('value', value)
                except Exception as e:
                    print(e)
                    value = f'Ошибка: {e}'

        if self.name == 'default':
            if hasattr(obj, serializer_field_name):
                try:
                    value = getattr(obj, serializer_field_name)
                except Exception as e:
                    print(e)
                    value = f'Ошибка: {e}'

        elif self.name == 'serializer':
            serializer = serializer_field.serializer
            if not serializer:
                value = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                if serializer_field.type == 'ForeignKey':
                    queryset = [getattr(obj, serializer_field_name)]
                elif serializer_field.type == 'OneToOneField':
                    queryset = [getattr(obj, serializer_field_name)]
                elif serializer_field.type == 'ManyToManyField':
                    queryset = getattr(obj, serializer_field_name).all()
                elif serializer_field.type == 'GenericForeignKey':
                    related_class = serializer.content_type.model_class()
                    queryset = related_class.objects.filter(
                        content_type=ContentType.objects.get_for_model(obj),
                        object_id=obj.id,
                    )       

                elif serializer_field.type == 'JSONField':
                    queryset = getattr(obj, serializer_field_name)            

                if not queryset or queryset == [None]:
                    value = None
                else:
                    value = serializer.get_data(queryset, data_type='list')
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'

        elif self.name == 'ForeignKey':
            try:
                rel_object = getattr(obj, serializer_field_name)
                if rel_object and hasattr(rel_object, 'id'):
                    value = rel_object.id
                else:
                    value = None
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'    

        elif self.name == 'OneToOneField':
            try:
                object = getattr(obj, serializer_field_name)
                value = object.id
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'  

        elif self.name == 'ManyToManyField':
            try:
                value = list(getattr(obj, serializer_field_name).all().values_list('id', flat=True))
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}' 

        elif self.name == 'FileField':
            try:
                file = getattr(obj, serializer_field_name)
                if not file:
                    value = None
                else:
                    value = file.url
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'           

        # print('value', value)   
        return value
    

class IncomingFieldHandler(Handler):
    """
        Класс, инструкция для обработки поля.
    """

    def get_transform_data(self, value, serializer_field: models.Model) -> type:
        field_error_data = {}
        transform_field_name = serializer_field.name
        transform_field_value = value

        if self.name == 'ForeignKey':
            try:
                if value is dict:
                    field_error_data[transform_field_name] = 'Обработчик ожидает идентификатор обьекта, но получил dict'

                else:
                    if 'id' not in transform_field_name:
                        transform_field_name += '_id'
                        # transform_field_value = int
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'  
                field_error_data[transform_field_name] = f'Ошибка: {e}'

        elif self.name == 'serializer':
            serializer = serializer_field.serializer
            if not serializer:
                field_error_data[transform_field_name] = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                if serializer_field.type == 'ForeignKey':
                    transform_field_value = serializer.deserialize(transform_field_value, method='POST').first()
                elif serializer_field.type == 'OneToOneField':
                    pass
                elif serializer_field.type == 'ManyToManyField':
                    pass
                elif serializer_field.type == 'GenericForeignKey':
                    pass                 
            except Exception as e:
                print(e)
                field_error_data[transform_field_name] = f'Ошибка: {e}'

        return transform_field_name, transform_field_value, field_error_data
    

class FormFieldHandler(Handler):
    """
    """

    def get_html(self, value, serializer_field: models.Model):
        html = ''

        if self.name == 'CharField':
            html = f"<input name='{serializer_field.name}' value='{value}'>"

        return html
    

class StructureFieldHandler(Handler):
    """
        Класс, инструкция для обработки поля.
    """

    def get_value(self, serializer_field: models.Model):
        value = ''
        print('get_value')
        print('self.name', self.name)

        if serializer_field.serializer:
            serializer = serializer_field.serializer
            if not serializer:
                value = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                value = serializer.get_structure()
            except Exception as e:
                print(e)
                value = f'Ошибка: {e}'

        return value