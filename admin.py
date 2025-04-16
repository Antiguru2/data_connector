from django.contrib import admin

from .models import *


@admin.register(SerializerField)
class SerializerFieldAdmin(admin.ModelAdmin):
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


