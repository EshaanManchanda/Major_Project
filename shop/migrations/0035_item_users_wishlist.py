# Generated by Django 4.1.7 on 2023-05-16 14:18

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0034_remove_company_coupon_category_sales_coupon_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='users_wishlist',
            field=models.ManyToManyField(blank=True, related_name='user_wishlist', to=settings.AUTH_USER_MODEL),
        ),
    ]
