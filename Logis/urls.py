from .views import entidades, upload, erase, distribuir, distrib_manual
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('urnas/', entidades.urna_list, name='urna_list'),
    path('municipios/', entidades.municipio_list, name='municipio_list'),
    path('secoes/', entidades.secao_list, name='secao_list'),
    path('zonas/', entidades.zona_list_selection, name='zona_list_selection'),
    path('zonas/list/', entidades.zona_list, name='zona_list'),
    path('upload/', upload.upload_file, name='uploadFile'),
    path('upload/success/', TemplateView.as_view(template_name="success.html"), name='upload_success'),
    path('limpar_tudo/', erase.delete_all_data, name='delete_all_data'),
    path('distribuir/', distribuir.distribuir_urnas, name='distribuir_urnas'),
    path('distribuicao/', distribuir.distribuicao_page, name='distribuicao_page'),
    path('distribution-history/', entidades.distribution_history, name='distribution_history'),
    path('distribuir-urnas-manual/', distrib_manual.manual_distribuir_urnas, name='manual_distribuir_urnas'),
    path('distributions/<str:zone_id>/<str:timestamp>/', entidades.distribution_detail, name='distribution_detail'),
    path('finalize-distribution/', distrib_manual.finalize_distribution, name='finalize_distribution'),
    path('reset-estoque/', entidades.reset_estoque, name='reset_estoque'),
    path('', entidades.home_view, name="home"),

]
