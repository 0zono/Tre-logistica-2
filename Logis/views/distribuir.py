from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
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

def get_stock_zone(stock_zona_id):
    """Função auxiliar que recebe qual zona é a estoque (entrada do usuário)"""
    try:
        return ZonaEleitoral.objects.get(id=stock_zona_id)
    except ZonaEleitoral.DoesNotExist:
        logger.error(f"Zona de estoque {stock_zona_id} não encontrada.")
        return None

def calculate_needs(target_zonas):
    """Calcula a quantidade total de urnas necessárias."""
    total_needed = sum(zona.qtdSecoes for zona in target_zonas)
    total_contingency = sum(int(zona.qtdSecoes * 0.12) for zona in target_zonas)
    return total_needed, total_contingency

def get_stock_inventory(stock_zona):
    """Cria dicionário com urnas em estoque e suas quantidades.."""
    stock_urnas = Urna.objects.filter(zona_eleitoral=stock_zona).order_by('-modelo')
    stock_inventory = {urna.modelo: urna.qtd for urna in stock_urnas}
    return stock_urnas, stock_inventory

def allocate_urnas(stock_urnas, stock_inventory, zona, needed, is_contingency=False):
    """Checa se a quantidade requerida está disponivel no estoqye"""
    distributions = []
    allocated = False
    for urna in stock_urnas:
        available = stock_inventory.get(urna.modelo, 0)
        if available >= needed:
            distributions.append({'modelo': urna.modelo, 'bio': urna.bio, 'qtd': needed, 'contingencia': is_contingency})
            stock_inventory[urna.modelo] -= needed
            allocated = True
            break
    return distributions, allocated

def create_distributions(stock_zona, user, zona, distributions):
    """Armazena distribuicao"""
    for dist in distributions:
        Distribuicao.objects.create(
            stock_zone=stock_zona,
            distributed_by=user,
            target_zones=str(zona.id),
            urna_modelo=dist['modelo'],
            urna_bio=dist['bio'],
            urna_contingencia=dist['contingencia'],
            urna_quantity=dist['qtd']
        )
        Urna.objects.create(
            modelo=dist['modelo'],
            bio=dist['bio'],
            zona_eleitoral=zona,
            qtd=dist['qtd'],
            contingencia=dist['contingencia']
        )

@login_required
def distribuir_urnas(request):
    if request.method == 'POST':
        stock_zona_id = request.POST.get('stock_zona_id')
        if not stock_zona_id:
            logger.error("Zona de estoque não selecionada.")
            return JsonResponse({'messages': ['Zona de estoque não selecionada.']}, status=400)
        
        stock_zona = get_stock_zone(stock_zona_id)
        if not stock_zona:
            return JsonResponse({'messages': ['Zona de estoque não encontrada.']}, status=404)
        
        target_zonas = ZonaEleitoral.objects.exclude(id=stock_zona_id)
        total_needed, total_contingency = calculate_needs(target_zonas)
        stock_urnas, stock_inventory = get_stock_inventory(stock_zona)
        total_stock = sum(stock_inventory.values())
        
        if total_stock < (total_needed + total_contingency):
            logger.error(f"Estoque insuficiente. Necessário: {total_needed + total_contingency}, Disponível: {total_stock}")
            return JsonResponse({'messages': ['Estoque insuficiente.']}, status=400)
        
        try:
            with transaction.atomic():
                Urna.objects.filter(zona_eleitoral__in=target_zonas).delete()
                sorted_zonas = sorted(target_zonas, key=lambda x: x.qtdSecoes, reverse=True)
                
                for zona in sorted_zonas:
                    regular_distributions, allocated = allocate_urnas(stock_urnas, stock_inventory, zona, zona.qtdSecoes)
                    if not allocated:
                        raise ValueError(f"Não foi possível alocar um único modelo para a zona {zona.id}")
                    
                    contingency_distributions, contingency_allocated = allocate_urnas(stock_urnas, stock_inventory, zona, int(zona.qtdSecoes * 0.12), is_contingency=True)
                    if not contingency_allocated:
                        raise ValueError(f"Não foi possível alocar urnas de contingência para a zona {zona.id}")
                    
                    create_distributions(stock_zona, request.user, zona, regular_distributions + contingency_distributions)
                
                for urna in stock_urnas:
                    urna.qtd = stock_inventory[urna.modelo]
                    urna.save()
            
            logger.info("Distribuição concluída com sucesso.")
            return JsonResponse({'messages': ['Distribuição concluída com sucesso.']})
        
        except ValueError as e:
            logger.error(f"Erro de validação: {str(e)}")
            return JsonResponse({'messages': [str(e)]}, status=400)
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            return JsonResponse({'messages': ['Erro durante a distribuição.']}, status=500)
    
    zonas = ZonaEleitoral.objects.all().order_by('id')
    return render(request, 'Logis/distribuicao_urnas.html', {'zonas': zonas})

def distribuicao_page(request):
    zonas = ZonaEleitoral.objects.all()
    return render(request, 'Logis/distribuicao_urnas.html', {'zonas': zonas})
