from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db import transaction
from ..models import ZonaEleitoral, Urna, Distribuicao

import logging

# Configure logging
logging.basicConfig(
    filename='distribuicao_urnas.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@login_required
def distribuir_urnas(request):
    if request.method == 'POST':
        stock_zona_id = request.POST.get('stock_zona_id')
        
        if not stock_zona_id:
            logger.error("Zona de estoque não selecionada.")
            return JsonResponse({'messages': ['Zona de estoque não selecionada.']}, status=400)
        
        logger.info(f"Iniciando processo de distribuição a partir da zona de estoque {stock_zona_id}")
        
        try:
            stock_zona = ZonaEleitoral.objects.get(id=stock_zona_id)
            logger.info(f"Zona de estoque encontrada: {stock_zona.id} - {stock_zona.nome}")
        except ZonaEleitoral.DoesNotExist:
            logger.error(f"Zona de estoque {stock_zona_id} não encontrada.")
            return JsonResponse({'messages': ['Zona de estoque não encontrada.']}, status=404)

        # Cálculo de necessidades
        target_zonas = ZonaEleitoral.objects.exclude(id=stock_zona_id)
        total_needed = sum(zona.qtdSecoes for zona in target_zonas)
        total_contingency = sum(int(zona.qtdSecoes * 0.12) for zona in target_zonas)
        
        # Verificação de estoque
        stock_urnas = Urna.objects.filter(zona_eleitoral=stock_zona).order_by('-modelo')
        total_stock = sum(urna.qtd for urna in stock_urnas)
        summary = []
        
        if total_stock < (total_needed + total_contingency):
            logger.error(f"Estoque insuficiente. Necessário: {total_needed + total_contingency}, Disponível: {total_stock}")
            return JsonResponse({
                'messages': [f'Estoque insuficiente. Necessário: {total_needed + total_contingency}, Disponível: {total_stock}']
            }, status=400)
        
        stock_inventory = {urna.modelo: urna.qtd for urna in stock_urnas}
        
        try:
            with transaction.atomic():
                # Limpar distribuições anteriores
                deleted_count = Urna.objects.filter(zona_eleitoral__in=target_zonas).delete()
                logger.info(f"Removidas {deleted_count[0]} urnas de distribuições anteriores")
                
                sorted_zonas = sorted(target_zonas, key=lambda x: x.qtdSecoes, reverse=True)
                target_zones_str = ",".join(str(zona.id) for zona in sorted_zonas)
                
                for zona in sorted_zonas:
                    regular_needed = zona.qtdSecoes
                    contingency_needed = int(regular_needed * 0.12)
                    
                    distributions = []
                    
                    # Distribuição de urnas regulares
                    regular_allocated = False
                    for urna in stock_urnas:
                        available = stock_inventory.get(urna.modelo, 0)
                        if available >= regular_needed:
                            distributions.append({
                                'modelo': urna.modelo,
                                'bio': urna.bio,
                                'qtd': regular_needed,
                                'contingencia': False
                            })
                            stock_inventory[urna.modelo] -= regular_needed
                            regular_allocated = True
                            
                            # Criar registro de distribuição para urnas regulares
                            Distribuicao.objects.create(
                                stock_zone=stock_zona,
                                distributed_by=request.user,
                                target_zones=str(zona.id),
                                urna_modelo=urna.modelo,
                                urna_bio=urna.bio,
                                urna_contingencia=False,
                                urna_quantity=regular_needed
                            )
                            break
                    
                    if not regular_allocated:
                        raise ValueError(f"Não foi possível alocar um único modelo para todas as urnas regulares da zona {zona.id}")
                    
                    # Distribuição de urnas de contingência
                    primary_model = distributions[0]['modelo']
                    compatible_models = ['2022', '2020'] if primary_model in ['2022', '2020'] else ['2022', '2020', '2015', '2013']
                    
                    remaining_contingency = contingency_needed
                    
                    # Distribuir urnas de contingência
                    for urna in stock_urnas.filter(modelo__in=compatible_models):
                        if remaining_contingency <= 0:
                            break
                            
                        available = stock_inventory.get(urna.modelo, 0)
                        if available > 0:
                            allocated = min(remaining_contingency, available)
                            distributions.append({
                                'modelo': urna.modelo,
                                'bio': urna.bio,
                                'qtd': allocated,
                                'contingencia': True
                            })
                            stock_inventory[urna.modelo] -= allocated
                            remaining_contingency -= allocated
                            
                            # Criar registro de distribuição para urnas de contingência
                            Distribuicao.objects.create(
                                stock_zone=stock_zona,
                                distributed_by=request.user,
                                target_zones=str(zona.id),
                                urna_modelo=urna.modelo,
                                urna_bio=urna.bio,
                                urna_contingencia=True,
                                urna_quantity=allocated
                            )
                    
                    if remaining_contingency > 0 and compatible_models != ['2022', '2020', '2015', '2013']:
                        older_models = ['2015', '2013']
                        for urna in stock_urnas.filter(modelo__in=older_models):
                            if remaining_contingency <= 0:
                                break
                                
                            available = stock_inventory.get(urna.modelo, 0)
                            if available > 0:
                                allocated = min(remaining_contingency, available)
                                distributions.append({
                                    'modelo': urna.modelo,
                                    'bio': urna.bio,
                                    'qtd': allocated,
                                    'contingencia': True
                                })
                                stock_inventory[urna.modelo] -= allocated
                                remaining_contingency -= allocated
                                
                                # Criar registro de distribuição para urnas de contingência antigas
                                Distribuicao.objects.create(
                                    stock_zone=stock_zona,
                                    distributed_by=request.user,
                                    target_zones=str(zona.id),
                                    urna_modelo=urna.modelo,
                                    urna_bio=urna.bio,
                                    urna_contingencia=True,
                                    urna_quantity=allocated
                                )
                    
                    if remaining_contingency > 0:
                        raise ValueError(f"Estoque insuficiente para zona {zona.id}. Faltam {remaining_contingency} urnas de contingência")
                    
                    # Criar registros de urnas
                    for dist in distributions:
                        Urna.objects.create(
                            modelo=dist['modelo'],
                            bio=dist['bio'],
                            zona_eleitoral=zona,
                            qtd=dist['qtd'],
                            contingencia=dist['contingencia']
                        )
                    
                    zona_summary = {
                        'zona': f"{zona.id} - {zona.nome}",
                        'distribuicoes': distributions
                    }
                    summary.append(zona_summary)
                
                # Atualizar estoque final
                for urna in stock_urnas:
                    urna.qtd = stock_inventory[urna.modelo]
                    urna.save()

            logger.info("Distribuição concluída com sucesso.")
            return JsonResponse({'messages': ['Distribuição concluída com sucesso.']})
            
        except ValueError as e:
            logger.error(f"Erro de validação: {str(e)}")
            return JsonResponse({'messages': [str(e)]}, status=400)
        except Exception as e:
            logger.error(f"Erro inesperado durante a distribuição: {str(e)}")
            logger.exception("Stacktrace completo:")
            return JsonResponse({'messages': [f'Erro durante a distribuição: {str(e)}']}, status=500)

    zonas = ZonaEleitoral.objects.all().order_by('id')
    return render(request, 'Logis/distribuicao_urnas.html', {'zonas': zonas})

def distribuicao_page(request):
    zonas = ZonaEleitoral.objects.all()
    return render(request, 'Logis/distribuicao_urnas.html', {'zonas': zonas})