from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Municipio, Urna, ZonaEleitoral, MunicipioZona, Secao
from django.db.models import Sum, Count
from django.http import JsonResponse
import logging
import pandas as pd
from django.core.files.storage import FileSystemStorage

class UploadFileForm(forms.Form):
    file = forms.FileField()   

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            if 'zonamun' in filename.lower():
                if check_all_tables_have_rows():
                    delete_existing_data()
                import_zonamun_data(file_path)
            elif 'secoes' in filename.lower():
                if check_all_tables_have_rows():
                    delete_existing_data()
                import_secoes_data(file_path)

            return redirect('Logis/sucess.html')
    else:
        form = UploadFileForm()
    return render(request, 'Logis/upload.html', {'form': form})

def check_all_tables_have_rows():
    return (
        ZonaEleitoral.objects.exists() and
        Municipio.objects.exists() and
        Secao.objects.exists()
    )

def delete_existing_data():
    ZonaEleitoral.objects.all().delete()
    Municipio.objects.all().delete()
    Secao.objects.all().delete()

def import_zonamun_data(file_path):
    zonamun_df = pd.read_excel(file_path)
    for _, row in zonamun_df.iterrows():
        cod_mun = row['COD_MUNIC']
        nome_municipio = row['NOM_MUNIC']

        municipio, created = Municipio.objects.get_or_create(
            cod=cod_mun,
            defaults={'nome': nome_municipio}
        )
        if not created:
            municipio.nome = nome_municipio
            municipio.save()

        zona, _ = ZonaEleitoral.objects.get_or_create(nome=str(row['COD_ZONA']))
        MunicipioZona.objects.get_or_create(municipio=municipio, zona=zona)

def import_secoes_data(file_path):
    secoes_df = pd.read_excel(file_path)
    for _, row in secoes_df.iterrows():
        zona_nome = str(row['COD_ZONA'])
        try:
            zona = ZonaEleitoral.objects.get(nome=zona_nome)
        except ZonaEleitoral.DoesNotExist:
            continue

        Secao.objects.create(
            cod_zona=zona,
            cod_municipio=str(row['COD_MUNIC']),
            cod_local=str(row['COD_LOCAL']),
            cod_secao=str(row['COD_SECAO']),
            ind_especial=str(row['IND_ESPECIAL'])
        )

        zona.qtdSecoes += 1
        zona.save()