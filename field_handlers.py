import re
import traceback

from datetime import datetime
from decimal import Decimal, InvalidOperation

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

        elif serializer_field.serializer:
            serializer = serializer_field.serializer

            if not serializer:
                value = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                serializer.data_type = serializer_field.data_type
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
                    value = serializer.get_data(queryset)
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
                # print('serializer_field_name', serializer_field_name)
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

        elif self.name == 'DateField':
            try:
                if getattr(obj, serializer_field_name):
                    value = getattr(obj, serializer_field_name).strftime('%d.%m.%Y')          
                else:
                    value = None
            except Exception as e:
                print('FieldHandler.get_value() error in DateField', e)
                value = f'Ошибка: {e}' 

        # print('value', value)   
        return value
    

class KeyFormFieldHandler(FieldHandler):
    """
        Класс, инструкция для обработки поля.
    """

    def get_value(self, obj, serializer_field: models.Model):
        return super().get_value(obj, serializer_field)

class IncomingFieldHandler(Handler):
    """
        Класс, инструкция для обработки поля.
    """

    def get_transform_data(self, value, serializer_field: models.Model) -> type:
        # print(f'KeyFormFieldHandler.get_transform_data()')
        field_error_data = {}
        transform_field_name = serializer_field.name
        transform_field_value = value

        # print(f'serializer_field.incoming_handler', serializer_field.incoming_handler)

        if serializer_field.incoming_handler == 'cargo_calc__route':
            delivery_route = DeliveryRoute.objects.create()
            for point in value:
                if point.get('name') == 'from_airport_code':
                    from_delivery_point, created = DeliveryPoint.objects.get_or_create(unic_code=point.get('value'))
                elif point.get('name') == 'to_airport_code':
                    to_delivery_point, created = DeliveryPoint.objects.get_or_create(unic_code=point.get('value'))

            route_segment, created = RouteSegment.objects.get_or_create(
                from_point=from_delivery_point, 
                to_point=to_delivery_point,
                transport_type=TransportType.objects.get(unic_code='AIR'),
            )
                
            delivery_route_segment = DeliveryRouteSegment.objects.create(
                delivery_route=delivery_route,
                route_segment=route_segment,
            )

            if serializer_field.real_field_name:
                transform_field_name = serializer_field.real_field_name

            transform_field_name += '_id'
            transform_field_value = delivery_route.id

        elif serializer_field.incoming_handler == 'cargo_calc__transit_route':
            delivery_route = DeliveryRoute.objects.create()

            delivery_route_segments_data = value[0].get('value')
            for delivery_route_segment_data in delivery_route_segments_data:
                for delivery_route_segment_field in delivery_route_segment_data:
                    if delivery_route_segment_field.get('name') == 'order':
                        order = delivery_route_segment_field.get('value')
                    if delivery_route_segment_field.get('name') == 'route_segment':
                        route_segment_data = delivery_route_segment_field.get('value')

                for item in route_segment_data:
                    unic_code = item.get('value')[0].get('value')
                    if item.get('name') == 'from_point':
                        from_point, created = DeliveryPoint.objects.get_or_create(unic_code=unic_code)
                    elif item.get('name') == 'to_point':
                        to_point, created = DeliveryPoint.objects.get_or_create(unic_code=unic_code)
                        
                route_segment, created = RouteSegment.objects.get_or_create(
                    from_point=from_point, 
                    to_point=to_point,
                    transport_type=TransportType.objects.get(unic_code='AIR'),
                )

                delivery_route_segment = DeliveryRouteSegment.objects.create(
                    delivery_route=delivery_route,
                    route_segment=route_segment,
                    order=order,
                )

            transform_field_name += '_id'
            transform_field_value = delivery_route.id
            
                    
        elif serializer_field.incoming_handler == 'cargo_calc__services':
            for item in value:
                service, service_data = serializer_field.serializer.deserialize(item)
                service.delivery_info = self.some_model
                service.save()

        elif serializer_field.incoming_handler == 'cargo_calc__prices':
            for item in value:
                price, price_data = serializer_field.serializer.deserialize(item)
                if self.some_model:
                    price.content_type = ContentType.objects.get_for_model(self.some_model)
                    price.object_id = self.some_model.id
                    price.name = 'price' if 'price' in serializer_field.name else serializer_field.name
                    price.save()




        elif serializer_field.serializer:
            # print(f'serializer_field.serializer: {serializer_field.serializer}')
            serializer = serializer_field.serializer
            try:
                # print('serializer_field.type', serializer_field.type)
                if serializer_field.type == 'ForeignKey':
                    kwargs = {}
                    id_field_name = serializer_field.field_name_for_method
                    id_field_value = None
                    if id_field_name:
                        for field_data in transform_field_value:
                            # print(f'field_data: {field_data}')
                            if field_data['name'] == id_field_name:
                                id_field_value = field_data.get('value')

                        if id_field_value:
                            kwargs['id_field_name'] = id_field_name
                            kwargs['id_field_value'] = id_field_value
                            
                    transform_field_value, error_data = serializer.deserialize(
                        value, 
                        method=serializer_field.incoming_method,
                        **kwargs
                    )
                    # print(f'transform_field_value: {transform_field_value}')
                    
                elif serializer_field.type == 'OneToOneField':
                    pass

                elif serializer_field.type == 'ManyToManyField':
                    # print('ManyToManyField 111')
                    validated_items = []
                    for item in value:
                        item_value, item_error = serializer.deserialize(
                            item,
                            method=serializer_field.incoming_method
                        )
                        if item_error:
                            field_error_data[transform_field_name] = item_error
                        else:
                            validated_items.append(item_value)
                    transform_field_value = validated_items

                elif serializer_field.type == 'PseudoManyToManyField':
                    # print('PseudoManyToManyField 111')
                    validated_items = []
                    for item in value:
                        model_class = serializer.content_type.model_class()
                        # print('model_class', model_class)
                        for some_model_field in model_class._meta.get_fields():
                            if some_model_field.related_model == self.some_model.__class__:
                                # print('break')
                                item[some_model_field.name] = self.some_model
                                item.append({
                                    'name': f'{some_model_field.name}_id',
                                    'value': self.some_model.id
                                })                                
                                break
                        # print('item', item)
                        item_value, item_error = serializer.deserialize(
                            item,
                            method=serializer_field.incoming_method
                        )
                        if item_error:
                            field_error_data[transform_field_name] = item_error
                        else:
                            validated_items.append(item_value)
                    transform_field_value = validated_items

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
            try:
                transform_field_value = datetime.strptime(transform_field_value, '%d.%m.%Y')
            except Exception as e:
                print('IncomingFieldHandler.get_transform_data() error in DateField', e)
                transform_field_value = None
                field_error_data[transform_field_name] = f'Ошибка: {e}'

        return transform_field_name, transform_field_value, field_error_data


class ValidateFieldHandler(Handler):
    """
        Класс, инструкция для валидации полей.
    """

    def validate(self, result_data, serializer_field: models.Model, level: int = 0, **kwargs):
        """
        Валидирует значение поля и возвращает данные с информацией о валидации.
        
        Args:
            value: Значение для валидации
            serializer_field: Поле сериализатора
            
        Returns:
            tuple: (данные с информацией о валидации, результат валидации)
        """
        value = result_data.get('value')
        result_data.update({
            'error_text': None,
            'info_text': None,
            'is_valid': True,
        })

        if serializer_field.name in ['to_airport_code', 'from_airport_code']:
            if not re.match(r'^[A-Z]{3}$', value):
                result_data.update({
                    'error_text': 'Код аэропорта должен содержать 3 буквы(XXX)',
                    'is_valid': False
                })

        elif serializer_field.name == 'transport_company':
            transport_company_unic_code = value[0].get('value')
            if not transport_company_unic_code:
                result_data.update({
                    'error_text': 'Транспортная компания не может быть пустой',
                    'is_valid': False
                })
            else:
                if not re.match(r'^[A-Z0-9]{2}$', transport_company_unic_code):
                    result_data.update({
                        'error_text': 'Код транспортной компании должен содержать 2 символа (буквы или цифры)',
                        'is_valid': False
                    })

        elif serializer_field.name == 'awb_num':
            # Должен быть в формате 550-66590878
            if not re.match(r'^[0-9]{3}-[0-9]{8}$', value):
                result_data.update({
                    'error_text': 'Номер AWB должен быть в формате 550-66590878',
                    'is_valid': False
                })

        elif serializer_field.serializer:
            serializer = serializer_field.serializer
            try:
                if serializer_field.type in ['ForeignKey', 'OneToOneField',]:
                    is_valid, data = serializer.validate(value, level=level+1)
                    result_data.update({
                        'is_valid': is_valid,
                        'value': data,
                    })
                    
                elif serializer_field.type == 'ManyToManyField':
                    validated_items = []
                    items_is_valid = True
                    
                    for item in value:
                        is_valid, data = serializer.validate(item, level=level+1)
                        validated_items.append(data)
                        if not is_valid:
                            items_is_valid = False
                            
                    result_data.update({
                        'is_valid': items_is_valid,
                        'value': validated_items
                    })

                    # Для time_price
                    if serializer_field.name in ['total_price', 'rate']:
                        # print("serializer_field.name in ['total_price', 'rate']")
                        # print("items_is_valid", items_is_valid)
                        # print("serializer_field.is_required", serializer_field.is_required)
                        if (not items_is_valid or value == []) and not serializer_field.is_required:
                            result_data.update({
                                'info_text': 'Значение не было определено',
                                'is_valid': True,
                                'value': []
                            })
                        # print("result_data", result_data)
                    
                elif serializer_field.type == 'GenericForeignKey':
                    pass                 
            except Exception as e:
                print('IncomingFieldHandler.validate() error in serializer', e)
                result_data.update({
                    'error_text': f'Ошибка: {e}',
                    'is_valid': False
                })

        elif serializer_field.type == 'IntegerField':
            try:
                int_value = int(value)
            except (ValueError, InvalidOperation):
                traceback.print_exc()
                result_data.update({
                    'value': None,
                    'info_text': 'Значение не было определено',
                })

        elif serializer_field.type == 'PositiveIntegerField':
            try:
                value = int(value)
                if value < 0:
                    raise ValueError('Значение должно быть положительным')
            except (ValueError, InvalidOperation):
                traceback.print_exc()
                result_data.update({
                    'value': None,
                    'info_text': 'Значение не было определено',
                })

        elif serializer_field.type == 'FloatField':
            try:
                float_value = float(value)
            except (ValueError, InvalidOperation):
                traceback.print_exc()
                result_data.update({
                    'value': None,
                    'info_text': 'Значение не было определено',
                })

        elif serializer_field.type == 'DecimalField':
            try:
                if isinstance(value, str):
                    # Удаляем пробелы и заменяем запятые на точки
                    value = value.strip().replace(' ', '').replace(',', '')
                result_data['value'] = str(Decimal(value))
            except:
                traceback.print_exc()
                result_data.update({
                    'value': None,
                    'info_text': 'Значение не было определено',
                })

        if result_data['value'] is None:
            if serializer_field.is_required:
                result_data.update({
                    'error_text': 'Поле не может быть пустым',
                    'info_text': 'Заполните поле',
                    'is_valid': False
                })
            else:
                if serializer_field.type in ['PositiveIntegerField', 'IntegerField', 'FloatField', 'DecimalField']:
                    result_data.update({
                        'value': 0,
                        'info_text': 'Значение не было определено, установлено 0',
                    })
                else:
                    result_data.update({
                        'value': '',
                        'info_text': 'Значение не было определено, установлено пустая строка',
                    })

        return result_data['is_valid'], result_data


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

    def get_value(self, serializer_field: models.Model, additional_field_keys: list = []):
        value = ''

        if serializer_field.serializer:
            serializer = serializer_field.serializer
            if not serializer:
                value = f'У поля сериализатора(SerializerField id={serializer_field.id}) не указан сериализатор'
            try:
                structure_data = serializer.get_structure(additional_field_keys=additional_field_keys)
                if serializer_field.type == 'ManyToManyField':
                    structure_data = [structure_data]
                    
                value = structure_data
            except Exception as e:
                print('StructureFieldHandler.get_value() error in serializer', e)
                value = f'Ошибка: {e}'

        return value