from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType

from calculator.models import DeliveryRoute, DeliveryRouteSegment, DeliveryPoint, RouteSegment, TransportType


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
                except Exception as e:
                    print('FieldHandler.get_value() error in isinstance(obj, models.Model)', e)
                    value = f'Ошибка: {e}'

        elif isinstance(obj, dict):
            obj: dict
            if serializer_field_name in obj.keys():
                try:
                    value = obj.get(serializer_field_name)
                    # print('value', value)
                except Exception as e:
                    print('FieldHandler.get_value() error in isinstance(obj, dict)', e)
                    value = f'Ошибка: {e}'

        if self.name == 'default':
            if hasattr(obj, serializer_field_name):
                try:
                    value = getattr(obj, serializer_field_name)
                except Exception as e:
                    print('FieldHandler.get_value() error in if hasattr(obj, serializer_field_name)', e)
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
                print('FieldHandler.get_value() error in serializer', e)
                value = f'Ошибка: {e}'

        elif self.name == 'ForeignKey':
            try:
                rel_object = getattr(obj, serializer_field_name)
                if rel_object and hasattr(rel_object, 'id'):
                    value = rel_object.id
                else:
                    value = None
            except Exception as e:
                print('FieldHandler.get_value() error in ForeignKey', e)
                value = f'Ошибка: {e}'    

        elif self.name == 'OneToOneField':
            try:
                object = getattr(obj, serializer_field_name)
                value = object.id
            except Exception as e:
                print('FieldHandler.get_value() error in OneToOneField', e)
                value = f'Ошибка: {e}'  

        elif self.name == 'ManyToManyField':
            try:
                value = list(getattr(obj, serializer_field_name).all().values_list('id', flat=True))
            except Exception as e:
                print('FieldHandler.get_value() error in ManyToManyField', e)
                value = f'Ошибка: {e}' 

        elif self.name == 'ManyToOneRel':
            try:
                value = getattr(obj, serializer_field_name).all().values_list('id', flat=True)
            except Exception as e:
                print('FieldHandler.get_value() error in ManyToOneRel', e)
                value = f'Ошибка: {e}'

        elif self.name == 'FileField':
            try:
                file = getattr(obj, serializer_field_name)
                if not file:
                    value = None
                else:
                    value = file.url
            except Exception as e:
                print('FieldHandler.get_value() error in FileField', e)
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

        if serializer_field.incoming_handler == 'cargo_calc__route':
            # print('!!!!!!!!!!!!!!!!!!!!!!!!  cargo_calc__route')
            delivery_route = DeliveryRoute.objects.create()
            for point in value:
                if point.get('name') == 'from_airport_code':
                    from_delivery_point, created = DeliveryPoint.objects.get_or_create(unic_code=point.get('value'))
                elif point.get('name') == 'to_airport_code':
                    to_delivery_point, created = DeliveryPoint.objects.get_or_create(unic_code=point.get('value'))

            # print('from_delivery_point', from_delivery_point)
            # print('to_delivery_point', to_delivery_point)

            route_segment, created = RouteSegment.objects.get_or_create(
                from_point=from_delivery_point, 
                to_point=to_delivery_point,
                transport_type=TransportType.objects.get(unic_code='AIR'),
            )
            # print('route_segment', route_segment)
                
            delivery_route_segment = DeliveryRouteSegment.objects.create(
                delivery_route=delivery_route,
                route_segment=route_segment,
            )

            # print('delivery_route_segment', delivery_route_segment)
            transform_field_name += '_id'
            transform_field_value = delivery_route.id

        elif serializer_field.incoming_handler == 'cargo_calc__services':
            # print('!!!!!!!!!!!!!!!!!!!!!!!!  cargo_calc__services')
            for item in value:
                service = serializer_field.serializer.deserialize(item, method='POST')
                # print('service', service)
                service.delivery_info = self.some_model
                service.save()
                # service_id = service.id
                # print('service_id', service_id)
                # transform_field_value = 
                # transform_field_value.append(service_id)

        elif serializer_field.incoming_handler == 'cargo_calc__prices':
            # print('!!!!!!!!!!!!!!!!!!!!!!!!  cargo_calc__prices')
            for item in value:
                price = serializer_field.serializer.deserialize(item, method='POST')
                # print('price', price)
                if self.some_model:
                    # print('self.some_model', self.some_model)
                    # price.related_object = self.some_model
                    price.content_type = ContentType.objects.get_for_model(self.some_model)
                    price.object_id = self.some_model.id
                    price.save()




        elif serializer_field.serializer:
            serializer = serializer_field.serializer
            if not serializer:
                field_error_data[transform_field_name] = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                for value in transform_field_value:
                    if serializer_field.type == 'ForeignKey':
                        transform_field_value = serializer.deserialize(value, method='POST')
                    elif serializer_field.type == 'OneToOneField':
                        pass
                    elif serializer_field.type == 'ManyToManyField':
                        ...
                    elif serializer_field.type == 'GenericForeignKey':
                        pass                 
            except Exception as e:
                print('IncomingFieldHandler.get_transform_data() error in serializer', e)
                field_error_data[transform_field_name] = f'Ошибка: {e}'

        elif self.name == 'ForeignKey':
            try:
                if value is dict:
                    field_error_data[transform_field_name] = 'Обработчик ожидает идентификатор обьекта, но получил dict'

                else:
                    if 'id' not in transform_field_name:
                        transform_field_name += '_id'
                        # transform_field_value = int
            except Exception as e:
                print('IncomingFieldHandler.get_transform_data() error in ForeignKey', e)
                value = f'Ошибка: {e}'  
                field_error_data[transform_field_name] = f'Ошибка: {e}'

        elif self.name == 'DateField':
            transform_field_value = datetime.strptime(transform_field_value, '%d.%m.%Y')


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
        # print('get_value')
        # print('self.name', self.name)

        if serializer_field.serializer:
            serializer = serializer_field.serializer
            if not serializer:
                value = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                structure_data = serializer.get_structure()
                if serializer_field.type == 'ManyToManyField':
                    structure_data = [structure_data]
                    
                value = structure_data
            except Exception as e:
                print('StructureFieldHandler.get_value() error in serializer', e)
                value = f'Ошибка: {e}'

        return value