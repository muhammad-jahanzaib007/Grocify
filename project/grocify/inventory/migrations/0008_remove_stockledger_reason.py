# Generated by Django 5.2.4 on 2025-07-15 10:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_stockledger_reason'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockledger',
            name='reason',
        ),
    ]
