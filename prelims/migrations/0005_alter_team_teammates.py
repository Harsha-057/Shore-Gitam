# Generated by Django 4.2.8 on 2023-12-27 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelims', '0004_team_teammates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='teammates',
            field=models.TextField(blank=True, max_length=5000),
        ),
    ]
