from django.db import models
from django.shortcuts import get_object_or_404, reverse
from django.contrib.auth.models import User
from django_countries.fields import CountryField


# Create your models here.
LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)
class Address(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
class comments(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    comment=models.TextField(null=True)
    images=models.ImageField(upload_to='comment',null=True)
    rating=models.FloatField(null=True)
    like=models.FloatField(null=True)
    dislike=models.FloatField(null=True)
    
class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()
    minCartValue = models.FloatField(default=True)

    def __str__(self):
        return self.code
    
class company(models.Model):
    name=models.CharField(max_length=20)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE)
    no_emp=models.FloatField(default=0)
    total_sales=models.FloatField(default=0)
    pending_order=models.FloatField(default=0)
    confirmed_order=models.FloatField(default=0)
    no_product=models.FloatField(default=0)
    coupon=models.ForeignKey(Coupon ,on_delete=models.CASCADE)
    
class Item(models.Model):
    company=models.OneToOneField(company,on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100, null=True)
    brand_Name=models.CharField(default='Not defined', max_length=20)
    price = models.FloatField(null=True)
    quantity = models.FloatField(null=True)
    discount_price = models.FloatField(blank=True, null=True)
    category = models.ForeignKey(
        'category', on_delete=models.SET_NULL, blank=True, null=True)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, null=True)
    slug = models.SlugField(unique=True, null=True)
    description_short = models.CharField(max_length=50, blank=True)
    description_long = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='Porduct', null=True)
    comments=models.ForeignKey(comments,on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })
        
class category(models.Model):
    category = models.CharField(max_length=25, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.category

class OrderItem(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        print(self.item.price)
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()
    
    
class Order(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    '''
    1. Item added to cart
    2. Adding a billing address
    (Failed checkout)
    3. Payment
    (Preprocessing, processing, packaging etc.)
    4. Being delivered
    5. Received
    6. Refunds
    '''

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total
    
