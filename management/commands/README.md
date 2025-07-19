# Система дампов данных для data_connector

Эта система позволяет создавать и загружать дампы данных для локальной разработки, учитывая особенности generic relations и сложных связей между моделями.

## Команды

### 1. create_dump

Создает дамп данных из базы данных в JSON формате.

**Использование:**
```bash
python manage.py create_dump [опции]
```

**Опции:**
- `--app APP` - Название приложения (по умолчанию: data_connector)
- `--output OUTPUT` - Название файла для сохранения дампа
- `--models MODEL [MODEL ...]` - Список моделей для включения в дамп
- `--exclude MODEL [MODEL ...]` - Список моделей для исключения из дампа

**Примеры:**
```bash
# Создать дамп всех моделей приложения
python manage.py create_dump

# Создать дамп с указанным именем файла
python manage.py create_dump --output my_dump.json

# Создать дамп только определенных моделей
python manage.py create_dump --models dataconnector serializerfield

# Создать дамп с исключением определенных моделей
python manage.py create_dump --exclude transmitterlog
```

### 2. load_dump

Загружает дамп данных из JSON файла в базу данных.

**Использование:**
```bash
python manage.py load_dump DUMP_FILE [опции]
```

**Опции:**
- `--app APP` - Название приложения (по умолчанию: data_connector)
- `--clear` - Очистить существующие данные перед загрузкой
- `--models MODEL [MODEL ...]` - Список моделей для загрузки

**Примеры:**
```bash
# Загрузить дамп
python manage.py load_dump my_dump.json

# Загрузить дамп с очисткой существующих данных
python manage.py load_dump my_dump.json --clear

# Загрузить только определенные модели
python manage.py load_dump my_dump.json --models dataconnector serializerfield

# Загрузить дамп из fixtures директории
python manage.py load_dump fixtures/my_dump.json
```

### 3. create_test_dump

Создает тестовые данные для проверки работы системы дампов.

**Использование:**
```bash
python manage.py create_test_dump [опции]
```

**Опции:**
- `--output OUTPUT` - Название файла для сохранения дампа (по умолчанию: test_dump.json)

**Примеры:**
```bash
# Создать тестовые данные
python manage.py create_test_dump

# Создать тестовые данные с указанным именем файла
python manage.py create_test_dump --output test_data.json
```

## Особенности работы с Generic Relations

Система специально разработана для работы с generic relations:

1. **При создании дампа:**
   - Сохраняется информация о ContentType и object_id
   - Добавляется дополнительная информация о связанном объекте
   - Обрабатываются все типы связей (ForeignKey, ManyToMany, GenericForeignKey)

2. **При загрузке дампа:**
   - Объекты создаются в два прохода для избежания проблем с зависимостями
   - Сначала создаются объекты без связей
   - Затем устанавливаются все связи между объектами
   - Generic relations восстанавливаются корректно

## Поддерживаемые типы полей

- **Базовые поля:** CharField, TextField, IntegerField, FloatField, BooleanField, DateField, DateTimeField, FileField
- **Связи:** ForeignKey, OneToOneField, ManyToManyField
- **Generic Relations:** GenericForeignKey
- **Специальные поля:** JSONField, SlugField, EmailField, URLField

## Структура дампа

Дамп сохраняется в формате JSON с следующей структурой:

```json
[
    {
        "model": "app_label.model_name",
        "pk": 1,
        "fields": {
            "field_name": "value",
            "foreign_key_field": 2,
            "many_to_many_field": [1, 2, 3],
            "content_type": 10,
            "object_id": 5,
            "generic_field_related": "app_label.model_name:5"
        }
    }
]
```

## Рекомендации по использованию

1. **Для разработки:** Создавайте дампы с тестовыми данными для локальной работы
2. **Для миграции:** Используйте `--clear` при загрузке для полной замены данных
3. **Для частичной загрузки:** Используйте `--models` для загрузки только нужных моделей
4. **Для безопасности:** Всегда делайте резервную копию перед загрузкой дампа

## Обработка ошибок

Система включает обработку ошибок:
- Пропуск объектов с ошибками сериализации
- Предупреждения о проблемах с связями
- Транзакционная загрузка для обеспечения целостности данных

## Файлы дампов

Дампы сохраняются в директории `fixtures/` приложения:
```
app/data_connector/fixtures/
├── my_dump.json
├── test_dump.json
└── zayavka.json 