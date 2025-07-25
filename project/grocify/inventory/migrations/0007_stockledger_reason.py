# Generated by Django 5.2.4 on 2025-07-15 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_auditlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockledger',
            name='reason',
            field=models.CharField(choices=[('purchase', 'Purchase'), ('sale', 'Sale'), ('damage', 'Damaged Goods'), ('theft', 'Theft'), ('expired', 'Expired'), ('adjustment', 'Manual Adjustment')], default='adjustment', max_length=20),
        ),
    ]
