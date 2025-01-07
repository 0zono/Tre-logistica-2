from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import Municipio, ZonaEleitoral, Secao, MunicipioZona, Urna, Distribuicao

def delete_all_data(request):
    if request.method == "POST":
        # Perform deletion
        Municipio.objects.all().delete()
        ZonaEleitoral.objects.all().delete()
        Secao.objects.all().delete()
        MunicipioZona.objects.all().delete()
        Urna.objects.all().delete()
        Distribuicao.objects.all().delete()
        
        # Add success message and redirect
        messages.success(request, "Todos os dados foram apagados com sucesso!")
        return redirect('secao_list')  # Redirect to a "home" or dashboard page (adjust as needed)

    return render(request, 'Logis/delete_all_data.html')
