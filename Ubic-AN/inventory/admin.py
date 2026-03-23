from django.contrib import admin
from .models import Recinto, Plano, Activo


@admin.register(Recinto)
class RecintoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'recinto', 'nivel')
    list_filter = ('recinto',)


@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'etiqueta', 'marca', 'modelo', 'numero_serie', 'ip', 'anydesk', 'ubicacion_texto', 'plano')
    list_filter = ('ant_centro', 'marca', 'plano')
    search_fields = ('usuario', 'etiqueta', 'numero_serie', 'ip', 'anydesk', 'ubicacion_texto', 'marca', 'modelo')
    list_per_page = 30

    fieldsets = (
        ('📍 Identificación del Equipo', {
            'fields': ('ant_centro', 'etiqueta', 'proveedor', 'ubicacion_texto', 'usuario', 'marca', 'modelo', 'numero_serie'),
        }),
        ('🖥️ Hardware', {
            'fields': ('cpu', 'ram', 'almacenamiento'),
        }),
        ('🌐 Red y Conectividad', {
            'fields': ('ip', 'contrasena_wifi', 'anydesk', 'pass_anydesk'),
        }),
        ('💿 Software', {
            'fields': ('version_win', 'licencia_office', 'pass_office', 'key_office'),
        }),
        ('📋 Información Adicional', {
            'fields': ('fecha_instalacion', 'comentarios', 'mac_managerlab', 'pass_managerlab'),
            'classes': ('collapse',),
        }),
        ('🗺️ Ubicación en Plano', {
            'fields': ('plano', 'coord_x', 'coord_y'),
        }),
    )

