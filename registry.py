from typing import Dict, Type, Optional
from .field_handlers import Handler

class FieldHandlerRegistry:
    """Реестр обработчиков полей для расширения функциональности data_connector"""
    
    def __init__(self):
        self._handlers: Dict[str, Dict[str, Type[Handler]]] = {
            'input': {},      # IncomingFieldHandler
            'validate': {},   # ValidateFieldHandler  
            'form': {},       # FormFieldHandler
            'structure': {},  # StructureFieldHandler
            'field': {}       # FieldHandler
        }
    
    def register_input_handler(self, field_name: str, handler_class: Type[Handler]):
        """Регистрирует обработчик входящих данных"""
        self._handlers['input'][field_name] = handler_class
    
    def register_validate_handler(self, field_name: str, handler_class: Type[Handler]):
        """Регистрирует обработчик валидации"""
        self._handlers['validate'][field_name] = handler_class
    
    def register_form_handler(self, field_name: str, handler_class: Type[Handler]):
        """Регистрирует обработчик форм"""
        self._handlers['form'][field_name] = handler_class
    
    def register_structure_handler(self, field_name: str, handler_class: Type[Handler]):
        """Регистрирует обработчик структуры"""
        self._handlers['structure'][field_name] = handler_class
        
    def register_field_handler(self, field_name: str, handler_class: Type[Handler]):
        """Регистрирует обработчик поля"""
        self._handlers['field'][field_name] = handler_class
    
    def get_handler(self, handler_type: str, field_name: str) -> Optional[Type[Handler]]:
        """Возвращает класс обработчика"""
        return self._handlers.get(handler_type, {}).get(field_name)
    
    def is_registered(self, handler_type: str, field_name: str) -> bool:
        """Проверяет, зарегистрирован ли обработчик"""
        return field_name in self._handlers.get(handler_type, {})

# Глобальный реестр
field_registry = FieldHandlerRegistry() 