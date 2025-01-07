from django.contrib import admin
from .models import Municipio, ZonaEleitoral, Secao, Urna, Distribuicao

# Register your models here.

@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cod')
    search_fields = ('nome', 'cod')

@admin.register(ZonaEleitoral)
class ZonaEleitoralAdmin(admin.ModelAdmin):
    list_display = ('nome', 'qtdSecoes')
    search_fields = ('nome',)

@admin.register(Secao)
class SecaoAdmin(admin.ModelAdmin):
    list_display = ('cod_secao', 'cod_zona', 'cod_municipio', 'cod_local', 'ind_especial')
    search_fields = ('cod_secao', 'cod_zona__nome', 'cod_municipio')

@admin.register(Urna)
class UrnaAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'bio', 'zona_eleitoral', 'qtd')
    list_filter = ('modelo', 'bio')
    search_fields = ('modelo', 'zona_eleitoral__nome')

@admin.register(Distribuicao)
class DistribuicaoAdmin(admin.ModelAdmin):
    list_display = ('stock_zone', 'distributed_by', 'created_at')
    search_fields = ('stock_zone__nome', 'distributed_by__username')

