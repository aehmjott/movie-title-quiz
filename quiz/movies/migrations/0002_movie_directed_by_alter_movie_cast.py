# Generated by Django 5.1 on 2024-08-12 13:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='directed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='direction_credits', to='movies.actor'),
        ),
        migrations.AlterField(
            model_name='movie',
            name='cast',
            field=models.ManyToManyField(blank=True, related_name='acting_credits', to='movies.actor'),
        ),
    ]
