# Generated by Django 4.1.7 on 2023-04-01 02:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0010_alter_orderitem_company'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='company',
        ),
    ]
