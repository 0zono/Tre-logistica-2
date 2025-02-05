from django.contrib import admin
from .models import Municipio, ZonaEleitoral, Secao, Urna, Distribuicao
from django.utils.html import format_html

@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cod')
    search_fields = ('nome', 'cod')
    ordering = ('nome',)

@admin.register(ZonaEleitoral)
class ZonaEleitoralAdmin(admin.ModelAdmin):
    list_display = ('nome', 'qtdSecoes')
    search_fields = ('nome',)
    ordering = ('nome',)

@admin.register(Secao)
class SecaoAdmin(admin.ModelAdmin):
    list_display = ('cod_secao', 'cod_zona', 'cod_municipio', 'cod_local', 'ind_especial')
    search_fields = ('cod_secao', 'cod_zona__nome', 'cod_municipio')
    list_filter = ('cod_zona', 'ind_especial')
    ordering = ('cod_zona', 'cod_secao')

@admin.register(Urna)
class UrnaAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'bio', 'zona_eleitoral', 'qtd', 'contingencia')
    list_filter = ('modelo', 'bio', 'contingencia')
    search_fields = ('modelo', 'zona_eleitoral__nome')
    ordering = ('-modelo', 'zona_eleitoral__nome')

@admin.register(Distribuicao)
class DistribuicaoAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'stock_zone',
        'distributed_by',
        'target_zones_display',
        'urna_info_display',
        'urna_quantity'
    )
    
    list_filter = (
        'created_at',
        'urna_modelo',
        'urna_bio',
        'urna_contingencia',
        'stock_zone',
        'distributed_by'
    )
    
    search_fields = (
        'stock_zone__nome',
        'distributed_by__username',
        'distributed_by__first_name',
        'distributed_by__last_name',
        'urna_modelo',
        'target_zones'
    )
    
    readonly_fields = (
        'created_at',
        'target_zones_display',
        'urna_info_display'
    )
    
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações da Distribuição', {
            'fields': (
                'stock_zone',
                'distributed_by',
                'target_zones',
                'created_at'
            )
        }),
        ('Detalhes da Urna', {
            'fields': (
                'urna_modelo',
                'urna_bio',
                'urna_contingencia',
                'urna_quantity'
            )
        })
    )

    def target_zones_display(self, obj):
        """Format target zones for better display"""
        return format_html("<span style='white-space: nowrap;'>{}</span>", obj.target_zones)
    target_zones_display.short_description = "Zonas Destino"
    target_zones_display.admin_order_field = 'target_zones'

    def urna_info_display(self, obj):
        """Combine urna information into a single column"""
        bio_status = "Bio" if obj.urna_bio else "Não Bio"
        tipo = "Contingência" if obj.urna_contingencia else "Regular"
        return format_html(
            "<span style='white-space: nowrap;'>{} - {} - {}</span>",
            obj.urna_modelo,
            bio_status,
            tipo
        )
    urna_info_display.short_description = "Informações da Urna"

    def get_readonly_fields(self, request, obj=None):
        
        if obj:  
            return self.readonly_fields + (
                'stock_zone',
                'distributed_by',
                'target_zones',
                'urna_modelo',
                'urna_bio',
                'urna_contingencia',
                'urna_quantity'
            )
        return self.readonly_fields

    class Media:
        css = {
            'all': ('admin/css/distribution.css',)
        }