from .views import views_distribuir, views_distribuir_manual, views_erase, views_upload, views_vizualizar
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('urnas/', views_vizualizar.urna_list, name='urna_list'),
    path('municipios/', views_vizualizar.municipio_list, name='municipio_list'),
    path('secoes/', views_vizualizar.secao_list, name='secao_list'),
    path('zonas/', views_vizualizar.zona_list_selection, name='zona_list_selection'),
    path('zonas/list/', views_vizualizar.zona_list, name='zona_list'),
    path('upload/', views_upload.upload_file, name='uploadFile'),
    path('upload/success/', views_upload.success_view, name='upload_success'),
    path('limpar_tudo/', views_erase.delete_all_data, name='delete_all_data'),
    path('distribuir/', views_distribuir.distribuir_urnas, name='distribuir_urnas'),
    path('distribuicao/', views_distribuir.distribuicao_page, name='distribuicao_page'),
    path('distribution-history/', views_vizualizar.distribution_history, name='distribution_history'),
    path('distribuir-urnas-manual/', views_distribuir_manual.manual_distribuir_urnas, name='manual_distribuir_urnas'),
    path('distributions/<str:zone_id>/<str:timestamp>/', views_vizualizar.distribution_detail, name='distribution_detail'),
    path('finalize-distribution/', views_distribuir_manual.finalizar_distribuicao, name='finalize_distribution'),
    path('reset-estoque/', views_vizualizar.reset_estoque, name='reset_estoque'),
    path('', views_vizualizar.home_view, name="home"),

]
