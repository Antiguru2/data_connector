# Система обработчиков полей Data Connector

## Обзор

Система обработчиков полей предоставляет гибкий и расширяемый механизм для обработки различных типов полей в Django-приложениях. Она позволяет разделить универсальную логику обработки данных от специфической бизнес-логики конкретных приложений.

## Архитектура

### Базовые компоненты

1. **Handler** - базовый класс для всех обработчиков
2. **FieldHandler** - обработка получения значений полей
3. **IncomingFieldHandler** - обработка входящих данных
4. **ValidateFieldHandler** - валидация полей
5. **FormFieldHandler** - генерация HTML форм
6. **StructureFieldHandler** - работа со структурой данных

### Реестр обработчиков

**FieldHandlerRegistry** - центральная система регистрации кастомных обработчиков, которая позволяет приложениям расширять функциональность data_connector без изменения его кода.

## Быстрый старт

### 1. Создание кастомных обработчиков

```python
# app/myapp/field_handlers.py
from data_connector.field_handlers import IncomingFieldHandler, ValidateFieldHandler
import re

class MyAppIncomingHandler(IncomingFieldHandler):
    """Обработчик входящих данных для приложения"""
    
    def get_transform_data(self, value, serializer_field):
        field_error_data = {}
        transform_field_name = serializer_field.name
        transform_field_value = value

        if self.name == 'my_custom_field':
            # Кастомная логика обработки
            processed_value = self.process_custom_field(value)
            return 'processed_field_name', processed_value, field_error_data
        
        # Для остальных полей вызываем родительский метод
        return super().get_transform_data(value, serializer_field)
    
    def process_custom_field(self, value):
        # Ваша логика обработки
        return value.upper()

class MyAppValidateHandler(ValidateFieldHandler):
    """Обработчик валидации для приложения"""
    
    def validate(self, result_data, serializer_field, level=0, **kwargs):
        value = result_data.get('value')
        
        # Валидация специфических полей
        if serializer_field.name == 'my_special_field':
            if not re.match(r'^[A-Z]{3}$', value):
                result_data.update({
                    'error_text': 'Поле должно содержать 3 заглавные буквы',
                    'is_valid': False
                })
                return result_data['is_valid'], result_data
        
        # Для остальных полей вызываем родительский метод
        return super().validate(result_data, serializer_field, level, **kwargs)
```

### 2. Регистрация обработчиков

```python
# app/myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        try:
            from data_connector.registry import field_registry
            from .field_handlers import MyAppIncomingHandler, MyAppValidateHandler
            
            # Регистрируем обработчики
            field_registry.register_input_handler('my_custom_field', MyAppIncomingHandler)
            field_registry.register_validate_handler('my_special_field', MyAppValidateHandler)
            
        except ImportError:
            # data_connector может быть не установлен
            pass
```

### 3. Использование в моделях

```python
# app/data_connector/models.py (пример использования в SerializerField)
class SerializerField(models.Model):
    name = models.CharField(max_length=100)
    incoming_handler = models.CharField(
        max_length=100, 
        choices=[
            ('my_custom_field', 'My Custom Field'),
            # другие варианты
        ]
    )
```

## Подробное руководство

### Типы обработчиков

#### 1. IncomingFieldHandler

Обрабатывает входящие данные и преобразует их в нужный формат.

**Основной метод:** `get_transform_data(value, serializer_field)`

**Возвращает:** `(field_name, field_value, error_data)`

```python
def get_transform_data(self, value, serializer_field):
    if self.name == 'my_handler':
        # Обработка данных
        processed_value = self.process_value(value)
        return 'processed_field', processed_value, {}
    
    return super().get_transform_data(value, serializer_field)
```

#### 2. ValidateFieldHandler

Валидирует данные полей.

**Основной метод:** `validate(result_data, serializer_field, level=0, **kwargs)`

**Возвращает:** `(is_valid, result_data)`

```python
def validate(self, result_data, serializer_field, level=0, **kwargs):
    value = result_data.get('value')
    
    if serializer_field.name == 'email':
        if '@' not in value:
            result_data.update({
                'error_text': 'Некорректный email',
                'is_valid': False
            })
    
    return result_data['is_valid'], result_data
```

#### 3. FieldHandler

Получает значения полей из объектов.

**Основной метод:** `get_value(obj, serializer_field, **kwargs)`

```python
def get_value(self, obj, serializer_field, **kwargs):
    if serializer_field.name == 'computed_field':
        return self.compute_special_value(obj)
    
    return super().get_value(obj, serializer_field, **kwargs)
```

#### 4. FormFieldHandler

Генерирует HTML элементы форм.

**Основной метод:** `get_html(value, serializer_field)`

```python
def get_html(self, value, serializer_field):
    if serializer_field.name == 'color_picker':
        return f'<input type="color" name="{serializer_field.name}" value="{value}">'
    
    return super().get_html(value, serializer_field)
```

#### 5. StructureFieldHandler

Работает со структурой данных.

**Основной метод:** `get_value(serializer_field, additional_field_keys=[])`

### Реестр обработчиков

#### Методы регистрации

```python
from data_connector.registry import field_registry

# Регистрация обработчиков входящих данных
field_registry.register_input_handler('field_name', HandlerClass)

# Регистрация валидаторов
field_registry.register_validate_handler('field_name', HandlerClass)

# Регистрация обработчиков полей
field_registry.register_field_handler('field_name', HandlerClass)

# Регистрация обработчиков форм
field_registry.register_form_handler('field_name', HandlerClass)

# Регистрация обработчиков структуры
field_registry.register_structure_handler('field_name', HandlerClass)
```

#### Методы получения

```python
# Получение обработчика
handler_class = field_registry.get_handler('input', 'field_name')

# Проверка регистрации
is_registered = field_registry.is_registered('validate', 'field_name')
```

## Лучшие практики

### 1. Группировка обработчиков

Создавайте один обработчик на тип операции для всего приложения:

```python
class MyAppIncomingHandler(IncomingFieldHandler):
    def get_transform_data(self, value, serializer_field):
        if self.name == 'field_type_1':
            return self.handle_type_1(value, serializer_field)
        elif self.name == 'field_type_2':
            return self.handle_type_2(value, serializer_field)
        
        return super().get_transform_data(value, serializer_field)
```

### 2. Обработка ошибок

Всегда оборачивайте логику в try-except:

```python
def get_transform_data(self, value, serializer_field):
    try:
        # Ваша логика
        return processed_data
    except Exception as e:
        return serializer_field.name, None, {serializer_field.name: f'Ошибка: {e}'}
```

### 3. Валидация

Используйте раннее возвращение для валидации:

```python
def validate(self, result_data, serializer_field, **kwargs):
    if serializer_field.name == 'my_field':
        if not self.is_valid(result_data['value']):
            result_data.update({'is_valid': False, 'error_text': 'Ошибка'})
            return False, result_data
    
    return super().validate(result_data, serializer_field, **kwargs)
```

### 4. Совместимость

Используйте try-except при импорте data_connector:

```python
def ready(self):
    try:
        from data_connector.registry import field_registry
        # регистрация обработчиков
    except ImportError:
        # data_connector не установлен
        pass
```

## Примеры использования

### Пример 1: Обработка файлов

```python
class FileProcessingHandler(IncomingFieldHandler):
    def get_transform_data(self, value, serializer_field):
        if self.name == 'image_upload':
            # Обработка загрузки изображения
            processed_image = self.resize_image(value)
            return 'processed_image_path', processed_image.path, {}
        
        return super().get_transform_data(value, serializer_field)
```

### Пример 2: Сложная валидация

```python
class BusinessValidationHandler(ValidateFieldHandler):
    def validate(self, result_data, serializer_field, **kwargs):
        if serializer_field.name == 'business_code':
            value = result_data.get('value')
            
            # Проверка по внешнему API
            if not self.validate_with_external_service(value):
                result_data.update({
                    'error_text': 'Код не найден в реестре',
                    'is_valid': False
                })
                return False, result_data
        
        return super().validate(result_data, serializer_field, **kwargs)
```

### Пример 3: Динамические формы

```python
class DynamicFormHandler(FormFieldHandler):
    def get_html(self, value, serializer_field):
        if serializer_field.name == 'country_selector':
            countries = self.get_countries_list()
            options = ''.join([f'<option value="{c.code}">{c.name}</option>' 
                             for c in countries])
            return f'<select name="{serializer_field.name}">{options}</select>'
        
        return super().get_html(value, serializer_field)
```

## Интеграция с SerializerFieldMixin

Система автоматически интегрируется с `SerializerFieldMixin`. Все методы `get_*_handler()` автоматически проверяют зарегистрированные обработчики:

```python
# В модели SerializerField
def get_input_handler(self):
    # Автоматически проверяет field_registry.get_handler('input', self.incoming_handler)
    # Если найден кастомный обработчик, возвращает его
    # Иначе возвращает стандартный IncomingFieldHandler
```

## Отладка

### Проверка регистрации

```python
from data_connector.registry import field_registry

# Проверить, зарегистрирован ли обработчик
print(field_registry.is_registered('input', 'my_field'))

# Получить класс обработчика
handler_class = field_registry.get_handler('validate', 'my_field')
print(handler_class.__name__ if handler_class else 'Not registered')
```

### Логирование

```python
import logging

class MyHandler(IncomingFieldHandler):
    def get_transform_data(self, value, serializer_field):
        logging.info(f"Processing field {serializer_field.name} with value {value}")
        # ваша логика
```

## Миграция существующего кода

Если у вас есть существующая логика в `field_handlers.py`, которую нужно вынести:

1. Создайте новый файл обработчиков в вашем приложении
2. Скопируйте специфическую логику
3. Зарегистрируйте обработчики в `apps.py`
4. Удалите старую логику из data_connector

Это обеспечит чистое разделение между универсальной и специфической логикой.

## Заключение

Система обработчиков полей обеспечивает:

- ✅ Модульность и расширяемость
- ✅ Разделение ответственности
- ✅ Легкость тестирования
- ✅ Обратную совместимость
- ✅ Чистую архитектуру

Используйте эту систему для создания гибких и поддерживаемых Django-приложений! 