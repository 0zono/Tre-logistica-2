from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import ZonaEleitoral, Urna, Distribuicao
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def manual_distribuir_urnas(request):
    """View for handling the urna distribution interface and process."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                stock_zona = get_object_or_404(ZonaEleitoral, nome='ZEestoque')
                
                # Validate input data
                if not isinstance(data, dict) or 'zones' not in data:
                    raise ValidationError('Formato de dados inválido')
                
                # Get current stock levels
                stock_urnas = {
                    urna.modelo: urna 
                    for urna in Urna.objects.filter(zona_eleitoral=stock_zona)
                }
                
                # Calculate total requirements and validate stock
                required_stock = {}
                for zone_data in data['zones']:
                    distributions = zone_data.get('distributions', {})
                    for model, qty in distributions.items():
                        if isinstance(qty, dict):  # Handle contingency
                            for cont_model, cont_qty in qty.items():
                                required_stock[cont_model] = required_stock.get(cont_model, 0) + cont_qty
                        else:
                            required_stock[model] = required_stock.get(model, 0) + qty

                # Validate stock availability
                for model, required_qty in required_stock.items():
                    stock_urna = stock_urnas.get(model)
                    if not stock_urna or required_qty > stock_urna.qtd:
                        available_qty = stock_urna.qtd if stock_urna else 0
                        raise ValidationError(
                            f'Estoque insuficiente para modelo {model}. '
                            f'Disponível: {available_qty}, Necessário: {required_qty}'
                        )

                # Process distributions
                for zone_data in data['zones']:
                    zone_id = zone_data['id']
                    distributions = zone_data.get('distributions', {})
                    zona = get_object_or_404(ZonaEleitoral, id=zone_id)
                    
                    # Clear existing distributions for this zone
                    Urna.objects.filter(zona_eleitoral=zona).delete()
                    
                    # Process regular urnas
                    for model, qty in distributions.items():
                        if model != 'contingency' and qty > 0:
                            # Update stock
                            stock_urna = stock_urnas[model]
                            stock_urna.qtd -= qty
                            stock_urna.save()
                            
                            # Create distribution
                            Urna.objects.create(
                                modelo=model,
                                bio=True,
                                zona_eleitoral=zona,
                                qtd=qty,
                                contingencia=False
                            )
                            
                            # Record distribution
                            Distribuicao.objects.create(
                                stock_zone=stock_zona,
                                distributed_by=request.user,
                                target_zones=str(zona.id),
                                urna_modelo=model,
                                urna_bio=True,
                                urna_contingencia=False,
                                urna_quantity=qty
                            )
                    
                    # Process contingency urnas
                    contingency_dist = distributions.get('contingency', {})
                    for model, qty in contingency_dist.items():
                        if qty > 0:
                            # Update stock
                            stock_urna = stock_urnas[model]
                            stock_urna.qtd -= qty
                            stock_urna.save()
                            
                            # Create distribution
                            Urna.objects.create(
                                modelo=model,
                                bio=True,
                                zona_eleitoral=zona,
                                qtd=qty,
                                contingencia=True
                            )
                            
                            # Record distribution
                            Distribuicao.objects.create(
                                stock_zone=stock_zona,
                                distributed_by=request.user,
                                target_zones=str(zona.id),
                                urna_modelo=model,
                                urna_bio=True,
                                urna_contingencia=True,
                                urna_quantity=qty
                            )
                
                logger.info(f"Distribution completed successfully by user {request.user}")
                return JsonResponse({'message': 'Distribuição concluída com sucesso'})
                
        except ValidationError as e:
            logger.warning(f"Validation error in distribution: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error during distribution: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

    # Handle GET request
    try:
        stock_zona = get_object_or_404(ZonaEleitoral, nome='ZEestoque')
        stock_urnas = Urna.objects.filter(zona_eleitoral=stock_zona)
        
        # Get zones excluding stock zone
        zonas = ZonaEleitoral.objects.exclude(id=stock_zona.id).order_by('id')
        urna_models = list(stock_urnas.values_list('modelo', flat=True).distinct().order_by('-modelo'))
        
        # Prepare zona data
        zonas_data = [
            {
                'id': zona.id,
                'nome': zona.nome,
                'qtdSecoes': zona.qtdSecoes
            }
            for zona in zonas
        ]
        
        # Prepare stock data
        stock_data = {
            'id': stock_zona.id,
            'nome': stock_zona.nome,
            'urnas': {
                urna.modelo: urna.qtd 
                for urna in stock_urnas
            }
        }
        
        context = {
            'zonas_json': json.dumps(zonas_data),
            'urna_models_json': json.dumps(urna_models),
            'stock_json': json.dumps(stock_data),
        }
        
        return render(request, 'Logis/manual_distribuicao_urnas.html', context)
        
    except Exception as e:
        logger.error(f"Error rendering distribution page: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Erro ao carregar a página'}, status=500)

@login_required
def finalize_distribution(request):
    """View for finalizing the distribution process."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        with transaction.atomic():
            data = json.loads(request.body)
            stock_zona = get_object_or_404(ZonaEleitoral, nome='ZEestoque')
            
            if not isinstance(data, dict) or 'zones' not in data:
                raise ValidationError('Formato de dados inválido')
            
            # Get current stock levels
            stock_urnas = {
                urna.modelo: urna 
                for urna in Urna.objects.filter(zona_eleitoral=stock_zona)
            }
            
            # Calculate and validate total requirements
            required_stock = {}
            for zone_data in data['zones']:
                distributions = zone_data.get('distributions', {})
                for model, qty in distributions.items():
                    if model == 'contingency':
                        for cont_model, cont_qty in qty.items():
                            required_stock[cont_model] = required_stock.get(cont_model, 0) + cont_qty
                    else:
                        required_stock[model] = required_stock.get(model, 0) + qty
            
            # Validate stock availability
            for model, required_qty in required_stock.items():
                stock_urna = stock_urnas.get(model)
                if not stock_urna or required_qty > stock_urna.qtd:
                    available_qty = stock_urna.qtd if stock_urna else 0
                    raise ValidationError(
                        f'Estoque insuficiente para modelo {model}. '
                        f'Disponível: {available_qty}, Necessário: {required_qty}'
                    )
            
            for zone_data in data['zones']:
                zone_id = zone_data['id']
                distributions = zone_data.get('distributions', {})
                zona = get_object_or_404(ZonaEleitoral, id=zone_id)
                
                # Remove existing distributions
                Urna.objects.filter(zona_eleitoral=zona).delete()
                
                # Process regular urnas
                for model, qty in distributions.items():
                    if model == 'contingency':
                        for cont_model, cont_qty in qty.items():
                            if cont_qty > 0:
                                # Update stock
                                stock_urna = stock_urnas[cont_model]
                                stock_urna.qtd -= cont_qty
                                stock_urna.save()
                                
                                # Create distribution
                                Urna.objects.create(
                                    modelo=cont_model,
                                    bio=True,
                                    zona_eleitoral=zona,
                                    qtd=cont_qty,
                                    contingencia=True
                                )
                                
                                # Record distribution
                                Distribuicao.objects.create(
                                    stock_zone=stock_zona,
                                    distributed_by=request.user,
                                    target_zones=str(zona.id),
                                    urna_modelo=cont_model,
                                    urna_bio=True,
                                    urna_contingencia=True,
                                    urna_quantity=cont_qty
                                )
                    elif qty > 0:
                        # Update stock
                        stock_urna = stock_urnas[model]
                        stock_urna.qtd -= qty
                        stock_urna.save()
                        
                        # Create distribution
                        Urna.objects.create(
                            modelo=model,
                            bio=True,
                            zona_eleitoral=zona,
                            qtd=qty,
                            contingencia=False
                        )
                        
                        # Record distribution
                        Distribuicao.objects.create(
                            stock_zone=stock_zona,
                            distributed_by=request.user,
                            target_zones=str(zona.id),
                            urna_modelo=model,
                            urna_bio=True,
                            urna_contingencia=False,
                            urna_quantity=qty
                        )
            
            logger.info(f"Distribution finalized successfully by user {request.user}")
            return JsonResponse({'message': 'Distribuição finalizada com sucesso'})
            
    except ValidationError as e:
        logger.warning(f"Validation error in finalization: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error during finalization: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)