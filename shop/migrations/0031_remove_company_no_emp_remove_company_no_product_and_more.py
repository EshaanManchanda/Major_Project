# Generated by Django 4.1.7 on 2023-04-07 14:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0030_slide_alter_item_date_published'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='no_emp',
        ),
        migrations.RemoveField(
            model_name='company',
            name='no_product',
        ),
        migrations.AlterField(
            model_name='item',
            name='date_published',
            field=models.DateTimeField(default=datetime.datetime(2023, 4, 7, 14, 8, 38, 253252, tzinfo=datetime.timezone.utc)),
        ),
    ]
