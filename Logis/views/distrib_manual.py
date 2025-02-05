from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import ZonaEleitoral, Urna, Distribuicao
import json
import logging


logger = logging.getLogger(__name__)

def get_stock():
    """Função auxiliar que recebe info sobre urnas no estoque"""
    stock_zona = get_object_or_404(ZonaEleitoral, nome='ZEestoque')
    stock_urnas = {urna.modelo: urna for urna in Urna.objects.filter(zona_eleitoral=stock_zona)}
    return stock_zona, stock_urnas

def validate_stock(required_stock, stock_urnas):
    """Checa se a quantidade requerida está disponivel no estoqye"""
    for model, required_qty in required_stock.items():
        stock_urna = stock_urnas.get(model)
        if not stock_urna or required_qty > stock_urna.qtd:
            available_qty = stock_urna.qtd if stock_urna else 0
            raise ValidationError(f'Estoque insuficiente para modelo {model}. Disponível: {available_qty}, Necessário: {required_qty}')

def process_distribution(data, user):
    """Processa a distribuição."""
    with transaction.atomic():
        stock_zona, stock_urnas = get_stock()
        
        if not isinstance(data, dict) or 'zones' not in data:
            raise ValidationError('Formato de dados inválido')
        
        required_stock = {}
        for zone_data in data['zones']:
            for model, qty in zone_data.get('distributions', {}).items():
                if isinstance(qty, dict):
                    for cont_model, cont_qty in qty.items():
                        required_stock[cont_model] = required_stock.get(cont_model, 0) + cont_qty
                else:
                    required_stock[model] = required_stock.get(model, 0) + qty
        
        validate_stock(required_stock, stock_urnas)
        
        for zone_data in data['zones']:
            zona = get_object_or_404(ZonaEleitoral, id=zone_data['id'])
            Urna.objects.filter(zona_eleitoral=zona).delete()
            
            for model, qty in zone_data.get('distributions', {}).items():
                if isinstance(qty, dict):
                    for cont_model, cont_qty in qty.items():
                        if cont_qty > 0:
                            stock_urnas[cont_model].qtd -= cont_qty
                            stock_urnas[cont_model].save()
                            Urna.objects.create(modelo=cont_model, bio=True, zona_eleitoral=zona, qtd=cont_qty, contingencia=True)
                            Distribuicao.objects.create(stock_zone=stock_zona, distributed_by=user, target_zones=str(zona.id), urna_modelo=cont_model, urna_bio=True, urna_contingencia=True, urna_quantity=cont_qty)
                elif qty > 0:
                    stock_urnas[model].qtd -= qty
                    stock_urnas[model].save()
                    Urna.objects.create(modelo=model, bio=True, zona_eleitoral=zona, qtd=qty, contingencia=False)
                    Distribuicao.objects.create(stock_zone=stock_zona, distributed_by=user, target_zones=str(zona.id), urna_modelo=model, urna_bio=True, urna_contingencia=False, urna_quantity=qty)
        
        logger.info(f"Distribution completed successfully by user {user}")
        return {'message': 'Distribuição concluída com sucesso'}

@login_required
def manual_distribuir_urnas(request):
    """View de distribuição. Renderiza o template que possui o código Vue.js para a distribuição"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            return JsonResponse(process_distribution(data, request.user))
        except ValidationError as e:
            logger.warning(f"Validation error in distribution: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error during distribution: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    try:
        stock_zona, stock_urnas = get_stock()
        zonas = ZonaEleitoral.objects.exclude(id=stock_zona.id).order_by('id')
        urna_models = list(stock_urnas.keys())
        
        context = {
            'zonas_json': json.dumps([{'id': zona.id, 'nome': zona.nome, 'qtdSecoes': zona.qtdSecoes} for zona in zonas]),
            'urna_models_json': json.dumps(urna_models),
            'stock_json': json.dumps({'id': stock_zona.id, 'nome': stock_zona.nome, 'urnas': {urna.modelo: urna.qtd for urna in stock_urnas.values()}}),
        }
        return render(request, 'Logis/manual_distribuicao_urnas.html', context)
    except Exception as e:
        logger.error(f"Error rendering distribution page: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Erro ao carregar a página'}, status=500)

@login_required
def finalize_distribution(request):
    """View que finaliza a distribuição"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    try:
        data = json.loads(request.body)
        return JsonResponse(process_distribution(data, request.user)) #IMPORTANTE
    except ValidationError as e:
        logger.warning(f"Validation error in finalization: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error during finalization: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
