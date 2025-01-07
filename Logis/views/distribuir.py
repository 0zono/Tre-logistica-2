from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import ZonaEleitoral, Urna, Distribuicao, DistributionLog
import math

def debug_log(message):
    print(f"DEBUG: {message}")

@csrf_exempt
def distribuir_urnas(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=400)

    try:
        stock_zona_id = request.POST.get('stock_zona_id')
        if not stock_zona_id:
            return JsonResponse({'error': 'Stock zona ID is required.'}, status=400)

        with transaction.atomic():
            stock_zona = ZonaEleitoral.objects.get(id=stock_zona_id)
            zonas = ZonaEleitoral.objects.exclude(id=stock_zona_id)
            urnas_por_zona = []  # Lista para armazenar a distribuição final

            # Remove urnas da zona de estoque
            urnas_disponiveis = Urna.objects.filter(zona_eleitoral=stock_zona)
            urnas_disponiveis_por_modelo = {}

            for urna in urnas_disponiveis:
                if urna.modelo not in urnas_disponiveis_por_modelo:
                    urnas_disponiveis_por_modelo[urna.modelo] = {'urnas': [], 'total_qtd': 0}
                urnas_disponiveis_por_modelo[urna.modelo]['urnas'].append(urna)
                urnas_disponiveis_por_modelo[urna.modelo]['total_qtd'] += urna.qtd

            for zona in zonas:
                secoes = zona.qtdSecoes
                if secoes <= 0:
                    continue

                # Define o modelo principal como o mais recente disponível
                modelo_principal = max(urnas_disponiveis_por_modelo.keys(), default=None)
                if not modelo_principal:
                    raise ValueError(f"Não há urnas disponíveis para a zona {zona.nome}.")

                # Calcula quantidade de urnas principais e de contingência
                urnas_principais = secoes
                urnas_contingencia = math.ceil(secoes * 0.15)

                # Garante que há urnas suficientes para o modelo principal
                if urnas_disponiveis_por_modelo[modelo_principal]['total_qtd'] < urnas_principais:
                    raise ValueError(f"Não há urnas suficientes do modelo {modelo_principal} para a zona {zona.nome}.")

                # Aloca urnas principais
                urnas_alocadas = []
                qtd_alocada = 0
                for urna in urnas_disponiveis_por_modelo[modelo_principal]['urnas']:
                    if qtd_alocada >= urnas_principais:
                        break

                    alocar = min(urna.qtd, urnas_principais - qtd_alocada)
                    urnas_alocadas.append((urna, alocar))
                    qtd_alocada += alocar
                    urna.qtd -= alocar
                    urna.save()

                # Determina compatibilidade para urnas de contingência
                modelos_compatíveis = []
                if modelo_principal == '2022':
                    modelos_compatíveis = ['2022', '2020']
                elif modelo_principal == '2020':
                    modelos_compatíveis = ['2020']

                urnas_compatíveis = []
                for modelo in modelos_compatíveis:
                    if modelo in urnas_disponiveis_por_modelo:
                        urnas_compatíveis.extend(urnas_disponiveis_por_modelo[modelo]['urnas'])

                urnas_contingencia_alocadas = []
                qtd_contingencia_alocada = 0
                for urna in urnas_compatíveis:
                    if qtd_contingencia_alocada >= urnas_contingencia:
                        break

                    alocar = min(urna.qtd, urnas_contingencia - qtd_contingencia_alocada)
                    urnas_contingencia_alocadas.append((urna, alocar))
                    qtd_contingencia_alocada += alocar
                    urna.qtd -= alocar

                if qtd_contingencia_alocada < urnas_contingencia:
                    raise ValueError(f"Não há urnas compatíveis suficientes para contingência na zona {zona.nome}.")

                # Cria o registro de distribuição
                distribuicao = Distribuicao.objects.create(
                    stock_zone=stock_zona,
                    distributed_by=request.user  # Assumindo que há autenticação e request.user é válido
                )

                # Cria novas instâncias de urna para a zona
                for urna, quantidade in urnas_alocadas:
                    Urna.objects.create(
                        modelo=urna.modelo,
                        bio=urna.bio,
                        zona_eleitoral=zona,
                        qtd=quantidade
                    )

                    DistributionLog.objects.create(
                        distribuicao=distribuicao,
                        urna=urna,
                        quantity=quantidade,
                        distribution_type='Principal'
                    )

                for urna, quantidade in urnas_contingencia_alocadas:
                    Urna.objects.create(
                        modelo=urna.modelo,
                        bio=urna.bio,
                        zona_eleitoral=zona,
                        qtd=quantidade
                    )

                    DistributionLog.objects.create(
                        distribuicao=distribuicao,
                        urna=urna,
                        quantity=quantidade,
                        distribution_type='Contingência'
                    )

                urnas_por_zona.append({
                    'zona': zona.nome,
                    'urnas_principais': [f"{urna.modelo} ({quantidade})" for urna, quantidade in urnas_alocadas],
                    'urnas_contingencia': [f"{urna.modelo} ({quantidade})" for urna, quantidade in urnas_contingencia_alocadas]
                })

            return JsonResponse({'success': True, 'distribuicao': urnas_por_zona})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



from django.shortcuts import render
from ..models import ZonaEleitoral

def distribuicao_page(request):
    zonas = ZonaEleitoral.objects.all()
    return render(request, 'Logis/distribuicao_urnas.html', {'zonas': zonas})