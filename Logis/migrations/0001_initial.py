# Generated by Django 5.1.4 on 2024-12-13 13:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('cod', models.CharField(max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Urna',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modelo', models.CharField(choices=[('2013', '2013'), ('2015', '2015'), ('2020', '2020'), ('2022', '2022')], max_length=4)),
                ('bio', models.BooleanField(default=True)),
                ('qtd', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ZonaEleitoral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, null=True)),
                ('qtdSecoes', models.IntegerField(default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Distribuicao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('distributed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('stock_zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distribuicoes', to='Logis.zonaeleitoral')),
            ],
        ),
        migrations.CreateModel(
            name='DistributionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('distribution_type', models.CharField(max_length=50)),
                ('distribuicao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distribution_logs', to='Logis.distribuicao')),
                ('urna', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Logis.urna')),
            ],
        ),
        migrations.AddField(
            model_name='urna',
            name='zona_eleitoral',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Logis.zonaeleitoral'),
        ),
        migrations.CreateModel(
            name='Secao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cod_municipio', models.CharField(max_length=8)),
                ('cod_local', models.CharField(max_length=10)),
                ('cod_secao', models.CharField(max_length=10)),
                ('ind_especial', models.CharField(max_length=1)),
                ('cod_zona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Logis.zonaeleitoral')),
            ],
        ),
        migrations.CreateModel(
            name='MunicipioZona',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('municipio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Logis.municipio')),
                ('zona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Logis.zonaeleitoral')),
            ],
        ),
    ]
