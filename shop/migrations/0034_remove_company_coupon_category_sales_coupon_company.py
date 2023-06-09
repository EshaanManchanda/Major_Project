# Generated by Django 4.1.7 on 2023-04-14 06:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0033_alter_item_date_published'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='coupon',
        ),
        migrations.AddField(
            model_name='category',
            name='sales',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='coupon',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='shop.company'),
        ),
    ]
