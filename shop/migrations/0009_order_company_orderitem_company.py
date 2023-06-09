# Generated by Django 4.1.7 on 2023-04-01 02:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_refund'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='shop.company'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='company',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='shop.company'),
            preserve_default=False,
        ),
    ]
