import time
import random
import string
import razorpay
import stripe
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm, CheckoutForm, CouponForm, RefundForm, PaymentForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from .decorators import unauthenticated_user, allowed_users
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View, TemplateView, FormView
from .models import wishlist,UserProfile
from shop.models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, AboutUs, ContactForm, category as Category,company,subcategory
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

stripe.api_key = settings.STRIPE_SECRET_KEY

class Author(DetailView):
    model = AboutUs
    template_name = "author.html"
    
class profile(DetailView):
    model = UserProfile
    template_name = "author.html"

def aboutus(request):
    data =AboutUs.objects.all()
    if request.method == "POST":
        ContactF = ContactForm()
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        ContactF.name = name
        ContactF.email = email
        ContactF.subject = subject
        ContactF.save()
        messages.success(request, "Successfully submitted you form")
    return render(request, "aboutus.html", {'data': data})

def successful(request):
    template = render_to_string(
        'account/email/order_successful.html', {'name': request.user.first_name})
    email = EmailMessage(
        'Thank you for purchasing',
        template,
        settings.EMAIL_HOST_USER,
        [request.user.email],
    )
    email.fail_silently = False
    email.send()


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)

def order_history(request,pk):
    pass_day=timezone.now()-timezone.timedelta(days=5)
    context = {
        'category': Category.objects.order_by('category'),
        'order': Order.objects.all().filter(user=pk).order_by('-ordered_date'),
        'refund_date':order_date_pass,
    }
    return render(request, "order_history.html",context)

def order_date_pass(request,date):
    pass_day=date-timezone.timedelta(days=7)
    return pass_day

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class HomeView(ListView):
    # model = Item
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        pass_day=timezone.now()-timezone.timedelta(days=5)
        context = super(HomeView, self).get_context_data(**kwargs)
        context.update({
            'category': Category.objects.order_by('category'),
            'item': Item.objects.all(),
            'time':timezone.now(),
            'time_pass':pass_day,
            
        })
        return context

    def get_queryset(self):
        self.item = Item.objects.filter(is_active=True)
        return self.item

def search(request):
    q=request.GET['q']
    data=Item.objects.filter(title__icontains=q)
    return render(request, 'search.html',{'data':data})   

class CatView(ListView):
    paginate_by = 4

    def get(self, *args, **kwargs):
        category = Category.objects.get(slug=self.kwargs['slug'])
        sub_cat=subcategory.objects.filter(main=category.id)
        item = Item.objects.filter(category=category, is_active=True)
        context = {
            'object_list': item,
            'category_title': category.category,
            'category_description': category.description,
            'category_image': category.image,
            'sub_cat':sub_cat,
        }
        return render(self.request, "category.html", context)

class subCatView(ListView):
    paginate_by = 4

    def get(self, *args, **kwargs):
        category = subcategory.objects.get(slug=self.kwargs['slug'])
        item = Item.objects.filter(subcategory=category, is_active=True)
        context = {
            'object_list': item,
            'category_title': category.name,
            # 'category_description': category.description,
            # 'category_image': category.image,
        }
        return render(self.request, "category.html", context)


@unauthenticated_user
def registerPage(request):
    form = CreateUserForm
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            group = Group.objects.get(name='customer')
            user.groups.add(group)
            messages.success(request, 'Account was created for ' + username)
            return redirect("user:login")

    context = {'form': form}
    return render(request, 'account/signup.html', context)


@unauthenticated_user
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user:home')
        else:
            messages.info(request, 'username or password is incorrect')

    return render(request, 'account/login.html')


def logoutUser(request):
    logout(request)
    return redirect('user:login')


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required(login_url='user:login')
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            time.sleep(1.5)
            return redirect("user:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            time.sleep(1.5)
            return redirect("user:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user,ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("user:order-summary")


@login_required(login_url='user:login')
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("user:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("user:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("user:product", slug=slug)


@login_required(login_url='user:login')
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("user:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("user:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("user:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("user:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("user:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("user:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("user:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("user:request-refund")

class Author(DetailView):
    model = AboutUs
    template_name = "author.html"
    
class FileFieldFormView(FormView):
    form_class = AboutUs
    template_name = 'upload.html'  # Replace with your template.
    success_url = '...'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                ...  # Do something with each file.
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class CheckoutView(View): 
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("user:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        print(self.request.POST)
        payment = Payment()
        bill = 0
        shipping = 0
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                        shipping = 1
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('user:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()
                        shipping = 1

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                        bill = 1
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('user:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()
                        bill = 1

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")
                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S' and bill == 1 and shipping == 1:
                    return redirect('user:payment', payment_option='stripe')
                elif payment_option == 'P' and bill == 1 and shipping == 1:
                    return redirect('user:payment', payment_option='paypal')
                elif payment_option == 'C' and bill == 1 and shipping == 1:
                    order_items = order.items.all()
                    for item in order_items:
                        item_save = Item.objects.get(slug=item.item.slug)
                        if item_save.quantity < item.quantity:
                            messages.warning(
                                self.request, f"please enter valid quantity {item_save.quantity} is available")
                            return redirect('user:order-summary')
                        else:
                            item_save.quantity = item_save.quantity-item.quantity
                            if item_save.quantity < 1:
                                item_save.is_active = False
                            item_save.save()
                            item.save()

                    order_items.update(ordered=True)
                    payment.user = self.request.user
                    payment.amount = order.get_total()
                    payment.save()
                    order.ordered = True
                    order.payment = payment
                    order.ref_code = create_ref_code()
                    order.save()

                    messages.success(
                        self.request, "Your order was successful!")
                    successful(self.request)
                    return redirect('/')
                else:
                    messages.warning(
                        self.request, "Invalid Entry selected")
                    return redirect('user:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("user:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("user:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="inr",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="inr",
                        source=token
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()
                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")

                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")
