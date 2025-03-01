from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse
from datetime import datetime
from ..models import Urna, Municipio, Secao, ZonaEleitoral, Distribuicao
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.db.models import Sum
from datetime import timedelta
from collections import defaultdict
from operator import itemgetter
    
def urna_list(request):
    query = request.GET.get('q', '')
    urna_queryset = Urna.objects.all()

    if query:
        urna_queryset = urna_queryset.filter(
            Q(modelo__icontains=query) |
            Q(zona_eleitoral__nome__icontains=query)
        )

    
    total_urnas = urna_queryset.aggregate(total=Sum('qtd'))['total'] or 0

    paginator = Paginator(urna_queryset, 10)
    page_number = request.GET.get('page')
    urnas = paginator.get_page(page_number)
    
    current_page = urnas.number
    total_pages = paginator.num_pages
    
    page_range = [
        x for x in range(current_page - 2, current_page + 3)
        if 1 <= x <= total_pages
    ]

    return render(request, 'Logis/list_urnas.html', {
        'urnas': urnas,
        'total_urnas': total_urnas,
        'query': query,
        'page_range': paginator.page_range,
        'total_pages': paginator.num_pages,
    })

def municipio_list(request):
    municipios = Municipio.objects.all()
    return render(request, 'Logis/list_municipio.html', {'municipios': municipios})

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

    
    current_page = secoes.number
    total_pages = paginator.num_pages

    page_range = [
        x for x in range(current_page - 2, current_page + 3)
        if 1 <= x <= total_pages
    ]

    return render(request, 'Logis/list_secao.html', {
        'secoes': secoes,
        'query': query,
        'page_range': page_range,
        'total_pages': total_pages,
    })


def zona_list(request):
    
    listing_type = request.GET.get('type', 'table')
    
    
    zonas = ZonaEleitoral.objects.exclude(nome='ZEestoque')
    
    
    total_secoes = sum(zona.qtdSecoes for zona in zonas)
    
    
    total_urnas_2022 = Urna.objects.filter(modelo='2022', contingencia=False).aggregate(total=models.Sum('qtd'))['total'] or 0
    total_urnas_2020 = Urna.objects.filter(modelo='2020', contingencia=False).aggregate(total=models.Sum('qtd'))['total'] or 0
    total_urnas_2015 = Urna.objects.filter(modelo='2015', contingencia=False).aggregate(total=models.Sum('qtd'))['total'] or 0
    total_urnas_2013 = Urna.objects.filter(modelo='2013', contingencia=False).aggregate(total=models.Sum('qtd'))['total'] or 0
    
    total_contingencia_2022 = Urna.objects.filter(modelo='2022', contingencia=True).aggregate(total=models.Sum('qtd'))['total'] or 0
    total_contingencia_2020 = Urna.objects.filter(modelo='2020', contingencia=True).aggregate(total=models.Sum('qtd'))['total'] or 0
    total_contingencia_2015 = Urna.objects.filter(modelo='2015', contingencia=True).aggregate(total=models.Sum('qtd'))['total'] or 0
    total_contingencia_2013 = Urna.objects.filter(modelo='2013', contingencia=True).aggregate(total=models.Sum('qtd'))['total'] or 0
    
    context = {
        'zonas': zonas,
        'total_secoes': total_secoes,
        'total_urnas_2022': total_urnas_2022,
        'total_urnas_2020': total_urnas_2020,
        'total_urnas_2015': total_urnas_2015,
        'total_urnas_2013': total_urnas_2013,
        'total_contingencia_2022': total_contingencia_2022,
        'total_contingencia_2020': total_contingencia_2020,
        'total_contingencia_2015': total_contingencia_2015,
        'total_contingencia_2013': total_contingencia_2013,
    }
    
    
    if listing_type == 'card':
        return render(request, 'Logis/list_zona_card.html', context)
    else:
        return render(request, 'Logis/list_zona_tabela.html', context)

def zona_list2(request):
    zonas = ZonaEleitoral.objects.all()
    total_secoes = sum(zona.qtdSecoes for zona in zonas)  
    return render(request, 'Logis/zona_list2.html', {'zonas': zonas, 'total_secoes': total_secoes})

def distribution_history(request):
    
    distributions = Distribuicao.objects.all().order_by('-created_at')
    
    
    distribution_groups = []
    current_group = []
    current_time = None
    
    for dist in distributions:
        if current_time is None:
            current_time = dist.created_at
            current_group = [dist]
        elif abs((dist.created_at - current_time).total_seconds()) <= 60:
            current_group.append(dist)
        else:
            if current_group:
                
                regular_totals = defaultdict(int)
                contingency_totals = defaultdict(int)
                total_urnas = 0
                
                for d in current_group:
                    if d.urna_contingencia:
                        contingency_totals[d.urna_modelo] += d.urna_quantity
                    else:
                        regular_totals[d.urna_modelo] += d.urna_quantity
                    total_urnas += d.urna_quantity
                
                distribution_groups.append({
                    'timestamp': current_time,
                    'distributor': current_group[0].distributed_by,
                    'stock_zone': current_group[0].stock_zone,
                    'distributions': current_group,
                    'regular_totals': dict(regular_totals),
                    'contingency_totals': dict(contingency_totals),
                    'total_urnas': total_urnas
                })
            
            current_time = dist.created_at
            current_group = [dist]
    
    if current_group:
        regular_totals = defaultdict(int)
        contingency_totals = defaultdict(int)
        total_urnas = 0
        
        for d in current_group:
            if d.urna_contingencia:
                contingency_totals[d.urna_modelo] += d.urna_quantity
            else:
                regular_totals[d.urna_modelo] += d.urna_quantity
            total_urnas += d.urna_quantity
            
        distribution_groups.append({
            'timestamp': current_time,
            'distributor': current_group[0].distributed_by,
            'stock_zone': current_group[0].stock_zone,
            'distributions': current_group,
            'regular_totals': dict(regular_totals),
            'contingency_totals': dict(contingency_totals),
            'total_urnas': total_urnas
        })
    
    return render(request, 'Logis/distribution_history.html', {'distribution_groups': distribution_groups})


def distribution_detail(request, zone_id, timestamp):
    try:
        timestamp_date = datetime.strptime(timestamp, '%Y-%m-%d-%H-%M')
    except ValueError:
        raise Http404("Invalid timestamp format")

    distributions = Distribuicao.objects.filter(
        created_at__date=timestamp_date.date(),
        created_at__hour=timestamp_date.hour,
        created_at__minute=timestamp_date.minute,
        stock_zone_id=zone_id
    ).select_related('stock_zone', 'distributed_by').order_by('urna_modelo')

    if not distributions.exists():
        raise Http404("Distribution group not found")

    first_dist = distributions.first()

    totals = {
        'regular': 0,
        'contingencia': 0,
        'bio': 0,
        'sem_bio': 0
    }

    modelo_summary = defaultdict(lambda: {
        'modelo': '',
        'regular': 0,
        'contingencia': 0,
        'bio': 0,
        'sem_bio': 0,
        'total': 0
    })

    
    for dist in distributions:
        summary = modelo_summary[dist.urna_modelo]
        summary['modelo'] = dist.urna_modelo
        
        if dist.urna_contingencia:
            summary['contingencia'] += dist.urna_quantity
            totals['contingencia'] += dist.urna_quantity
        else:
            summary['regular'] += dist.urna_quantity
            totals['regular'] += dist.urna_quantity
        
        if dist.urna_bio:
            summary['bio'] += dist.urna_quantity
            totals['bio'] += dist.urna_quantity
        else:
            summary['sem_bio'] += dist.urna_quantity
            totals['sem_bio'] += dist.urna_quantity
            
        summary['total'] += dist.urna_quantity

    
    modelo_summary = sorted(
        modelo_summary.values(),
        key=lambda x: x['modelo'],
        reverse=True
    )

    
    total_urnas = sum(model['total'] for model in modelo_summary)

    context = {
        'distribution': first_dist,
        'distributions': distributions,
        'modelo_summary': modelo_summary,
        'totals': totals,
        'total_urnas': total_urnas,
    }

    return render(request, 'Logis/distribution_detail.html', context)


def zona_list_selection(request):
    return render(request, 'Logis/list_zona_selecao.html')

def home_view(request):
    context = {
        'total_municipios': Municipio.objects.count(),
        'total_zonas': ZonaEleitoral.objects.count(),
        'total_urnas': Urna.objects.count()
    }
    return render(request, 'Logis/home.html', context)

def reset_estoque(request):
    if request.method == 'POST':
        try:
            # Retrieve the quantities from the request
            modelo_2022 = int(request.POST.get('modelo_2022', 0))
            modelo_2020 = int(request.POST.get('modelo_2020', 0))
            modelo_2015 = int(request.POST.get('modelo_2015', 0))
            modelo_2013 = int(request.POST.get('modelo_2013', 0))

            # Fetch the ZEestoque zone (assuming it always exists)
            estoque_zone = ZonaEleitoral.objects.get(nome='ZEestoque')

            # Define models and their quantities
            modelos = {
                '2022': modelo_2022,
                '2020': modelo_2020,
                '2015': modelo_2015,
                '2013': modelo_2013,
            }

            # Ensure each urna entry exists, updating or creating as needed
            for modelo, quantidade in modelos.items():
                urna, created = Urna.objects.get_or_create(
                    zona_eleitoral=estoque_zone, modelo=modelo,
                    defaults={'qtd': quantidade}
                )
                if not created:
                    urna.qtd = quantidade
                    urna.save()

            return JsonResponse({
                'status': 'success',
                'message': f'Estoque resetado: 2022: {modelo_2022}, 2020: {modelo_2020}, 2015: {modelo_2015}, 2013: {modelo_2013}'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro: {str(e)}'
            }, status=500)

    try:
        # Fetch the ZEestoque zone (assuming it always exists)
        estoque_zone = ZonaEleitoral.objects.get(nome='ZEestoque')

        # Fetch current stock quantities
        current_stock = {
            modelo: Urna.objects.filter(zona_eleitoral=estoque_zone, modelo=modelo)
                                .aggregate(total=Sum('qtd'))['total'] or 0
            for modelo in ['2022', '2020', '2015', '2013']
        }
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao recuperar estoque: {str(e)}'
        }, status=500)

    return render(request, 'Logis/geren_reset_estoque.html', {'current_stock': current_stock})


