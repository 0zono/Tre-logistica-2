# Generated by Django 5.1.4 on 2025-01-17 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Logis', '0002_urna_contingencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='distribuicao',
            name='urna_bio',
            field=models.BooleanField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='distribuicao',
            name='urna_contingencia',
            field=models.BooleanField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='distribuicao',
            name='urna_modelo',
            field=models.CharField(default=1, max_length=4),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='distribuicao',
            name='urna_quantity',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='DistributionLog',
        ),
    ]
