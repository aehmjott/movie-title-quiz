# Generated by Django 5.1 on 2024-08-12 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0002_movie_directed_by_alter_movie_cast'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Actor',
            new_name='Person',
        ),
    ]
