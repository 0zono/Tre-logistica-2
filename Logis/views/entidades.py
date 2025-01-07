from django.shortcuts import render
from ..models import Urna, Municipio, Secao, ZonaEleitoral
from django.core.paginator import Paginator
from django.db.models import Q

def urna_list(request):
    query = request.GET.get('q', '')
    urna_queryset = Urna.objects.all()

    if query:
        urna_queryset = urna_queryset.filter(
            Q(modelo__icontains=query) |
            Q(zona_eleitoral__nome__icontains=query)
        )

    paginator = Paginator(urna_queryset, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    urnas = paginator.get_page(page_number)

    # Calculate the visible page range
    current_page = urnas.number
    total_pages = paginator.num_pages
    page_range = [
        x for x in range(current_page - 2, current_page + 3)
        if 1 <= x <= total_pages
    ]

    return render(request, 'Logis/urna_list.html', {
        'urnas': urnas,
        'query': query,
        'page_range': page_range,
        'total_pages': total_pages,
    })


def municipio_list(request):
    municipios = Municipio.objects.all()
    return render(request, 'Logis/municipio_list.html', {'municipios': municipios})

def secao_list(request):
    query = request.GET.get('q', '')
    secao_queryset = Secao.objects.all()

    if query:
        secao_queryset = secao_queryset.filter(
            Q(cod_secao__icontains=query) |
            Q(cod_zona__nome__icontains=query) |
            Q(cod_municipio__icontains=query) |
            Q(cod_local__icontains=query)
        )

    paginator = Paginator(secao_queryset, 10)
    page_number = request.GET.get('page')
    secoes = paginator.get_page(page_number)

    # Calculate the visible page range
    current_page = secoes.number
    total_pages = paginator.num_pages
    page_range = [
        x for x in range(current_page - 2, current_page + 3)
        if 1 <= x <= total_pages
    ]

    return render(request, 'Logis/secao_list.html', {
        'secoes': secoes,
        'query': query,
        'page_range': page_range,
        'total_pages': total_pages,
    })

def zona_list(request):
    zonas = ZonaEleitoral.objects.all()
    return render(request, 'Logis/zona_list.html', {'zonas': zonas})
