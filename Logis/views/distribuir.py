from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db import transaction
from ..models import ZonaEleitoral, Urna, Distribuicao, DistributionLog

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
        
        logger.info(f"Necessidade total: {total_needed} urnas regulares + {total_contingency} urnas de contingência")
        logger.info(f"Total de zonas a receber urnas: {target_zonas.count()}")
        
        # Verificação de estoque
        stock_urnas = Urna.objects.filter(zona_eleitoral=stock_zona).order_by('-modelo')
        total_stock = sum(urna.qtd for urna in stock_urnas)
        summary = []
        
        logger.info("Estoque disponível por modelo:")
        for urna in stock_urnas:
            logger.info(f"Modelo {urna.modelo}: {urna.qtd} unidades (Bio: {urna.bio})")
        
        if total_stock < (total_needed + total_contingency):
            logger.error(f"Estoque insuficiente. Necessário: {total_needed + total_contingency}, Disponível: {total_stock}")
            return JsonResponse({
                'messages': [f'Estoque insuficiente. Necessário: {total_needed + total_contingency}, Disponível: {total_stock}']
            }, status=400)
        
        # Criar cópia do estoque
        stock_inventory = {urna.modelo: urna.qtd for urna in stock_urnas}
        logger.info(f"Inventário inicial: {stock_inventory}")
        
        try:
            with transaction.atomic():
                # Limpar distribuições anteriores
                deleted_count = Urna.objects.filter(zona_eleitoral__in=target_zonas).delete()
                logger.info(f"Removidas {deleted_count[0]} urnas de distribuições anteriores")
                
                # Ordenar zonas por tamanho para tentar distribuir urnas mais novas para zonas maiores
                sorted_zonas = sorted(target_zonas, key=lambda x: x.qtdSecoes, reverse=True)
                
                for zona in sorted_zonas:
                    logger.info(f"\nIniciando distribuição para zona {zona.id} - {zona.nome}")
                    regular_needed = zona.qtdSecoes
                    contingency_needed = int(regular_needed * 0.12)
                    logger.info(f"Necessidade da zona: {regular_needed} regulares + {contingency_needed} contingência")
                    
                    distributions = []
                    
                    # Modificação principal: tentar cada modelo até encontrar um que possa suprir toda a necessidade
                    regular_allocated = False
                    for urna in stock_urnas:
                        available = stock_inventory.get(urna.modelo, 0)
                        if available >= regular_needed:
                            # Este modelo tem quantidade suficiente para toda a zona
                            distributions.append({
                                'modelo': urna.modelo,
                                'bio': urna.bio,
                                'qtd': regular_needed,
                                'contingencia': False
                            })
                            stock_inventory[urna.modelo] -= regular_needed
                            regular_allocated = True
                            logger.info(f"Alocadas {regular_needed} urnas regulares modelo {urna.modelo} (restam {stock_inventory[urna.modelo]} no estoque)")
                            break
                    
                    if not regular_allocated:
                        logger.error(f"Não foi possível alocar um único modelo para todas as urnas regulares da zona {zona.id}")
                        raise ValueError(f"Não foi possível alocar um único modelo para todas as urnas regulares da zona {zona.id}")
                    
                    # Determinar modelo principal usado (agora garantidamente único)
                    primary_model = distributions[0]['modelo']
                    
                    # Definir modelos compatíveis para contingência
                    all_models = ['2022', '2020', '2015', '2013']
                    if primary_model in ['2022', '2020']:
                        compatible_models = ['2022', '2020']  # Primeiro tenta modelos mais novos
                    else:
                        compatible_models = all_models  # Pode usar qualquer modelo
                    
                    logger.info(f"Modelo usado para urnas regulares: {primary_model}")
                    logger.info(f"Modelos compatíveis para contingência: {compatible_models}")
                    
                    # Distribuir urnas de contingência
                    remaining_contingency = contingency_needed
                    logger.info("Iniciando distribuição de urnas de contingência")
                    
                    # Primeira tentativa com modelos preferenciais
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
                            logger.info(f"Alocadas {allocated} urnas de contingência modelo {urna.modelo} (restam {stock_inventory[urna.modelo]} no estoque)")
                    
                    # Se ainda precisar de contingência e estiver usando apenas modelos novos, tenta modelos mais antigos
                    if remaining_contingency > 0 and compatible_models != all_models:
                        logger.info("Tentando usar modelos mais antigos para contingência")
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
                                logger.info(f"Alocadas {allocated} urnas de contingência modelo {urna.modelo} (restam {stock_inventory[urna.modelo]} no estoque)")
                                
                    
                    if remaining_contingency > 0:
                        logger.error(f"Estoque insuficiente para zona {zona.id}. Faltam {remaining_contingency} urnas de contingência")
                        raise ValueError(f"Estoque insuficiente para zona {zona.id}. Faltam {remaining_contingency} urnas de contingência")
                    
                    # Criar registros de urnas
                    logger.info("Criando registros no banco de dados")
                    for dist in distributions:
                        Urna.objects.create(
                            modelo=dist['modelo'],
                            bio=dist['bio'],
                            zona_eleitoral=zona,
                            qtd=dist['qtd'],
                            contingencia=dist['contingencia']
                        )
                        logger.info(f"Registro criado: {dist['qtd']} urnas modelo {dist['modelo']} ({'contingência' if dist['contingencia'] else 'regular'})")
                    zona_summary = {
                        'zona': f"{zona.id} - {zona.nome}",
                        'distribuicoes': [
                            {
                                'modelo': dist['modelo'],
                                'qtd': dist['qtd'],
                                'contingencia': dist['contingencia']
                            }
                            for dist in distributions
                        ]
                    }
                    summary.append(zona_summary)

                
                # Atualizar estoque final
                logger.info("\nAtualizando estoque final")
                for urna in stock_urnas:
                    urna.qtd = stock_inventory[urna.modelo]
                    urna.save()
                    logger.info(f"Estoque final modelo {urna.modelo}: {urna.qtd} unidades")
                logger.info("Resumo da distribuição por zona:")
                for zona_summary in summary:
                    logger.info(f"Zona {zona_summary['zona']}:")
                    for dist in zona_summary['distribuicoes']:
                        tipo = "Contingência" if dist['contingencia'] else "Regular"
                        logger.info(f" - {dist['qtd']} urnas modelo {dist['modelo']} ({tipo})")

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
