from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import Municipio, ZonaEleitoral, Secao, MunicipioZona, Urna, Distribuicao

def delete_all_data(request):
    if request.method == "POST":
        # VIEW PARA LIMPAR POR COMPLETO O SISTEMA, INCLUINDO HISTÓRICO
        Municipio.objects.all().delete()
        ZonaEleitoral.objects.all().delete()
        Secao.objects.all().delete()
        MunicipioZona.objects.all().delete()
        Urna.objects.all().delete()
        Distribuicao.objects.all().delete()
        
        
        messages.success(request, "Todos os dados foram apagados com sucesso!")
        return redirect('secao_list')  

    return render(request, 'Logis/delete_all_data.html')
