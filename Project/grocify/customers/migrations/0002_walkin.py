from django.db import migrations

def create_walkin(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    Customer.objects.get_or_create(
        phone='0000000000',
        defaults={'name': 'Walk-In Customer', 'points': 0}
    )

class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_walkin),
    ]