from django.db import models
from django.contrib.auth.models import User


class Municipio(models.Model):
    nome = models.CharField(max_length=100)
    cod = models.CharField(max_length=8)

    def __str__(self):
        return self.nome
    
class ZonaEleitoral(models.Model):
    nome = models.CharField(max_length=100, null=True)
    qtdSecoes = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.nome
    
class Secao(models.Model):
    cod_zona = models.ForeignKey(ZonaEleitoral, on_delete=models.CASCADE) #secao pertence a zona
    cod_municipio = models.CharField(max_length=8)
    cod_local = models.CharField(max_length=10)
    cod_secao = models.CharField(max_length=10)
    ind_especial = models.CharField(max_length=1)

    def __str__(self):
        return f"Secao {self.cod_secao} - Zona {self.cod_zona.nome} ({self.cod_zona.qtdSecoes})"

class MunicipioZona(models.Model): #relação entre municipio e zona. (vários para vários)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    zona = models.ForeignKey(ZonaEleitoral, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.municipio.nome} - {self.zona.nome}"
    
class Urna(models.Model):
    MODELO_URNAS = [
        ('2013', '2013'),
        ('2015', '2015'),
        ('2020', '2020'),
        ('2022', '2022'),
    ]
    modelo = models.CharField(
        max_length=4,
        choices=MODELO_URNAS
    )
    bio = models.BooleanField(default=True)  # Suporte a biometria
    zona_eleitoral = models.ForeignKey(ZonaEleitoral, on_delete=models.CASCADE)  # Urna pertence a uma zona eleitoral
    qtd = models.IntegerField(default=0)
    contingencia = models.BooleanField(default=False)

    def __str__(self):
        return self.modelo

class Distribuicao(models.Model):
    stock_zone = models.ForeignKey(ZonaEleitoral, related_name='distribuicoes', on_delete=models.CASCADE)
    distributed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    
    target_zones = models.CharField(max_length=255)  # Armazena o NOME da zona para qual a urna foi distribuida

    # Campos de informação de urna. Não podem ser resolvidos por uma chave estrangeira pois a tabela pode não existir mais no sistema.
    urna_modelo = models.CharField(max_length=4)  
    urna_bio = models.BooleanField()  
    urna_contingencia = models.BooleanField() 
    urna_quantity = models.IntegerField() 

    def __str__(self):
        return f"Distribuição {self.created_at} - Zona {self.stock_zone.nome}"
