import os

from django.contrib import admin
from django.conf import settings
from django.template.loader import render_to_string

from .models import *

BASE_DIR = settings.BASE_DIR

class AdminModelWithDataConnectorMenu(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if 'data_connector_menu' not in readonly_fields:
            readonly_fields.append('data_connector_menu')
        return readonly_fields
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'data_connector_menu' not in fields:
            fields.append('data_connector_menu')
        return fields
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if fieldsets and not any('data_connector_menu' in fieldset[1]['fields'] for fieldset in fieldsets):

            fieldsets.append(('Меню коннекторов', {
                'fields': ('data_connector_menu',),
            }))   

        return fieldsets  
    
    @admin.display(description="Коннектор данных 💾🔄")
    def data_connector_menu(self, obj):
        some_content_type = ContentType.objects.get_for_model(obj)
        default_list_url = f'/data_connector/super-api/{some_content_type.app_label}__{some_content_type.model.lower()}/'
        context = {
            'default_list_url': default_list_url,
        }  
        if obj.id:
            context['default_url'] = f'{default_list_url}{obj.id}/'

        data_connectors = DataConnector.objects.filter(content_type=some_content_type)
        data_connectors_list = []
        for connector in data_connectors:
            data_connectors_list.append({
                'list_url': f'{default_list_url}0/none/{connector.slug}/',
                'obj_url': f'{default_list_url}{obj.id}/none/{connector.slug}/',
                'connector': connector,
            })
        context['data_connectors'] = data_connectors_list

        context['create_new_data_connector_url'] = DataConnector.get_admin_create_url({
            'content_type': some_content_type.id,
            'name': obj._meta.verbose_name,
        })

        template_path = os.path.join(
            BASE_DIR, 
            'data_connector/templates', 
            'custom_admin/data_connector_menu.html'
        )

        return render_to_string(template_path, context)

@admin.register(SerializerField)
class SerializerFieldAdmin(AdminModelWithDataConnectorMenu):
    search_fields = [
        'id',
        'name',
        'verbose_name',
    ]
    list_display = [
        '__str__',
        'verbose_name',
        'type',
        'is_active',
    ]
    list_filter = [
        'data_connector',
        'is_active',
        'type',
    ]
    


class SerializerFieldInline(
    admin.StackedInline, 
):
    model = SerializerField
    ordering = [
        '-is_active',
        'id', 
]
    fk_name = 'data_connector'
    verbose_name = SerializerField._meta.verbose_name
    verbose_name_plural = SerializerField._meta.verbose_name_plural
    show_change_link = True
    # view_on_site = False   
    extra = 0
    # fields = [
    #     'name',
    #     'method',
    # ] 


@admin.register(DataConnector)
class DataConnectorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',), } 
    search_fields = [
        'id',
        'name',
        'slug',
    ]
    list_display = [
        '__str__',
        'is_active',
        'content_type',
    ]
    list_filter = [ 
        'content_type',
    ]
    fieldsets = [
        (None, {
            'fields': (
                'name',
                'slug',
                'description',
                'content_type',
                'additional_buttons',
            )
        }),
        ('Разрешения', {
            'fields': (
                'is_active',
                (
                    'is_allow_view',
                    'is_allow_edit',
                    'is_allow_delete',
                    'is_allow_create',                    
                ),
            )
        }),
        ('Дополнительное', {
            'fields': (
                'order',
                'created',
                'modified',
                'is_publish',
            ),
            "classes": ["wide", "collapse"],
        }), 
    ] 
    # fields = [
    #     'name',
    #     'slug',
    #     'description',
    #     'order',
    #     'is_publish',
    #     'content_type',
    #     'is_action',
    #     'additional_buttons',
    # ]
    # autocomplete_fields = [
    #     'content_type',
    # ]
    readonly_fields = [
        'modified',
        'created',
        'additional_buttons',
    ]
    save_as = True
    inlines = [
        SerializerFieldInline,
    ]


@admin.register(RemoteSite)
class RemoteSiteAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
        'name',
        'domain',
    ]


@admin.register(TransmitterLog)
class TransmitterLogAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
    ]


class TransmitterLogInline(
    admin.StackedInline, 
):
    model = TransmitterLog
    verbose_name = TransmitterLog._meta.verbose_name
    verbose_name_plural = TransmitterLog._meta.verbose_name_plural
    show_change_link = True
    # view_on_site = False   
    extra = 0
    
    # fields = [
    #     'name',
    #     'method',
    # ] 


@admin.register(Transmitter)
class TransmitterAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
        'name',
    ]
    # readonly_fields = [
    #     'buttons',
    # ]
    inlines = [
        TransmitterLogInline,
    ]


