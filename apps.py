from django.apps import AppConfig


class DataConnectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_connector'
    verbose_name = 'Коннектор данных'

    def ready(self) -> None:
        import data_connector.signals