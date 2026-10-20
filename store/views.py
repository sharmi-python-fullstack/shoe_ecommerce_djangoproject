from decimal import Decimal

from django.conf import settings
from django.http import Http404, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import EmailField
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.password_validation import validate_password
from .models import ContactInquiry, Product, Cart, CartItem, Order, OrderItem, NewsletterSubscription

def _get_checkout_items(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        items = [
            (item.product, item.quantity, item.size)
            for item in cart.items.select_related('product')
        ] if cart else []
        total = cart.total_price if cart else Decimal('0.00')
        return items, total

    cart_data = request.session.get('cart', {})
    product_ids = [int(product_id) for product_id in cart_data]
    products = Product.objects.filter(id__in=product_ids)
    product_map = {product.id: product for product in products}
    items = []
    total = Decimal('0.00')
    for product_id, value in cart_data.items():
        product = product_map.get(int(product_id))
        if product:
            cart_item = _session_cart_item(value)
            quantity = int(cart_item['quantity'])
            items.append((product, quantity, cart_item['size']))
            total += product.price * quantity
    return items, total


def _order_belongs_to_request(order, request):
    if request.user.is_authenticated:
        return order.user_id == request.user.pk
    return (
        order.user_id is None
        and request.session.session_key
        and order.checkout_session_key == request.session.session_key
    )


def _clear_order_items(order, request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            for item in order.items.all():
                cart.items.filter(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    size=item.size,
                ).delete()
        return

    cart_data = request.session.get('cart', {})
    for item in order.items.all():
        key = str(item.product_id)
        current = cart_data.get(key)
        if current is None:
            continue
        cart_item = _session_cart_item(current)
        if int(cart_item['quantity']) == item.quantity and cart_item['size'] == item.size:
            del cart_data[key]
    request.session['cart'] = cart_data
    request.session.modified = True


def product_list(request):
    """Display the searchable, filterable storefront and supplied image gallery."""
    products = Product.objects.all()
    search_query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip().lower()
    style_query = request.GET.get('style', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    if category in dict(Product.CATEGORY_CHOICES):
        products = products.filter(category=category)
    if style_query:
        products = products.filter(
            Q(name__icontains=style_query) | Q(description__icontains=style_query)
        )

    showcase_images = [
        {'path': f'images/figma_assets/image-{number}.png', 'label': f'StepUp style {number - 3}'}
        for number in range(4, 44)
    ]
    showcase_images.extend([
        {'path': f'images/figma_assets/{filename}', 'label': label}
        for filename, label in [
            ('image-46.png', 'Leather casual shoe'),
            ('125098_2_B02.20240229000136.jpg', 'Navy slip-on shoe'),
            ('12552_2_B02.20240226000125.jpg', 'Blush slip-on shoe'),
            ('14832_2_B02.20250530000126.jpg', 'Silver diamante heel'),
            ('14833_2_B02.20250530000126.jpg', 'Silver ankle-strap heel'),
            ('20741_2_B02.20240304000134.jpg', 'Kids printed trainer'),
            ('292091_2_B02.20240807000251.jpg', 'Kids pink sandal'),
            ('830166_2_B02.20240925000409.jpg', 'Navy running trainer'),
            ('830252_2_B02.20240925000249.jpg', 'White running trainer'),
            ('IMG_20250530_194909_340.jpg', 'Scarlet statement heel'),
            ('IMG_20250530_195525_107.jpg', 'Silver occasion heel'),
            ('IMG_20250530_195628_196.jpg', 'Smart leather shoes'),
        ]
    ])
    campaign_slides = [
        {
            'image': 'images/figma_assets/IMG_20250530_194707_093.jpg',
            'eyebrow': '',
            'title': 'Flat 50% Sale',
            'description': 'kids shoes',
            'link': '#collection-kids',
        },
        {
            'image': 'images/figma_assets/IMG_20250530_195525_107.jpg',
            'eyebrow': '',
            'title': 'Womens High Heels',
            'description': 'Flat 30% offer for your first order',
            'link': '?category=women#products',
        },
        {
            'image': 'images/figma_assets/IMG_20250530_195628_196.jpg',
            'eyebrow': '',
            'title': 'Mens wear high heel office shoe',
            'description': 'Only 40% discount today only',
            'link': '?category=men#products',
        },
        {
            'image': 'images/figma_assets/IMG_20250530_194909_340.jpg',
            'eyebrow': '',
            'title': 'Womens red color high heel for party',
            'description': 'For your first order get a free gift',
            'link': '?category=women#products',
        },
    ]
    category_label = dict(Product.CATEGORY_CHOICES).get(category, '')
    return render(
        request,
        'store/product_list.html',
        {
            'products': products,
            'search_query': search_query,
            'category': category,
            'category_label': category_label,
            'style_query': style_query,
            'showcase_images': showcase_images,
            'campaign_slides': campaign_slides,
        },
    )


def about(request):
    return render(request, 'store/about.html')


def contact(request):
    if request.method == 'POST':
        try:
            email = EmailField().clean(request.POST.get('email', '')).lower()
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            inquiry = request.POST.get('message', '').strip()
            if not name or not inquiry:
                raise ValidationError('Please enter your name and message.')
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            ContactInquiry.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=inquiry,
            )
            messages.success(request, 'Thanks for contacting StepUp. We will be in touch soon.')
            return redirect('store:contact')
    elif request.method != 'GET':
        return HttpResponseNotAllowed(['GET', 'POST'])
    return render(request, 'store/contact.html')


def account(request):
    User = get_user_model()
    mode = request.POST.get('mode', request.GET.get('mode', 'login'))
    if mode not in {'login', 'register'}:
        mode = 'login'
    errors = []
    email = request.POST.get('email', '').strip().lower()
    next_url = request.POST.get('next', request.GET.get('next', ''))

    if request.method == 'POST':
        password = request.POST.get('password', '')
        if mode == 'login':
            user_record = User.objects.filter(email__iexact=email).first()
            username = user_record.get_username() if user_record else email
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                    return redirect(next_url)
                return redirect('store:product_list')
            errors.append('Email or password was not recognized.')
        else:
            password_confirm = request.POST.get('password_confirm', '')
            try:
                email = EmailField().clean(email).lower()
                if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
                    raise ValidationError('An account with this email already exists.')
                validate_password(password)
                if password != password_confirm:
                    raise ValidationError('The passwords do not match.')
            except ValidationError as error:
                errors.extend(error.messages)
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                )
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Your StepUp account has been created.')
                return redirect('store:product_list')
    elif request.method != 'GET':
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(
        request,
        'store/account.html',
        {'mode': mode, 'errors': errors, 'email': email, 'next': next_url},
    )


def newsletter_subscribe(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        email = EmailField().clean(request.POST.get('email', '')).lower()
    except ValidationError:
        messages.error(request, 'Enter a valid email address to subscribe.')
        return redirect('store:product_list')

    _, created = NewsletterSubscription.objects.get_or_create(email=email)
    if created:
        messages.success(request, 'You are subscribed to StepUp.in updates.')
    else:
        messages.info(request, 'That email is already subscribed.')
    return redirect('store:product_list')


def product_detail(request, slug):
    """Show details for a single product identified by its slug."""
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/product_detail.html', {'product': product})

def _get_cart(request):
    """Utility to obtain the cart for the current user or session.
    For simplicity, only authenticated users get a persistent Cart.
    Anonymous users get a temporary cart stored in the session.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    return request.session.get('cart', {})


def _save_session_cart(request, cart_data):
    request.session['cart'] = cart_data
    request.session.modified = True


def _session_cart_item(value):
    if isinstance(value, dict):
        return {'quantity': value.get('quantity', 1), 'size': value.get('size', '')}
    return {'quantity': value, 'size': ''}


def _product_sizes(product):
    first, last = (25, 35) if product.category == 'kids' else (36, 46)
    return [str(size) for size in range(first, last + 1)]


def _default_product_size(product):
    return '30' if product.category == 'kids' else '41'


def add_to_cart(request, product_id):
    """Add a product to the cart (POST only)."""
    product = get_object_or_404(Product, pk=product_id)
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'size': _default_product_size(product)},
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        cart_data = request.session.get('cart', {})
        key = str(product_id)
        if key in cart_data:
            cart_item = _session_cart_item(cart_data[key])
            cart_item['quantity'] = int(cart_item['quantity']) + 1
        else:
            cart_item = {
                'quantity': 1,
                'size': _default_product_size(product),
            }
        cart_data[key] = cart_item
        _save_session_cart(request, cart_data)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def cart_detail(request):
    """Display and update the current user's shopping cart."""
    if request.method == 'POST':
        action = request.POST.get('action')
        quantity_value = request.POST.get('quantity', '')
        size_value = request.POST.get('size', '')
        if action not in {'update', 'remove'}:
            return HttpResponseNotAllowed(['GET', 'POST'])

        if request.user.is_authenticated:
            item = get_object_or_404(
                CartItem,
                pk=request.POST.get('item_id'),
                cart__user=request.user,
            )
            if action == 'remove':
                item.delete()
            else:
                try:
                    quantity = int(quantity_value)
                    if not 1 <= quantity <= 99:
                        raise ValueError
                except ValueError:
                    messages.error(request, 'Choose a quantity from 1 to 99.')
                else:
                    item.quantity = quantity
                    update_fields = ['quantity']
                    if size_value:
                        if size_value not in _product_sizes(item.product):
                            messages.error(request, 'Choose a valid shoe size.')
                            return redirect('store:cart_detail')
                        item.size = size_value
                        update_fields.append('size')
                    item.save(update_fields=update_fields)
        else:
            cart_data = request.session.get('cart', {})
            product_id = request.POST.get('product_id', '')
            if product_id not in cart_data:
                messages.error(request, 'That item is no longer in your cart.')
            elif action == 'remove':
                del cart_data[product_id]
                _save_session_cart(request, cart_data)
            else:
                try:
                    quantity = int(quantity_value)
                    if not 1 <= quantity <= 99:
                        raise ValueError
                except ValueError:
                    messages.error(request, 'Choose a quantity from 1 to 99.')
                else:
                    cart_item = _session_cart_item(cart_data[product_id])
                    cart_item['quantity'] = quantity
                    if size_value:
                        product = get_object_or_404(Product, pk=product_id)
                        if size_value not in _product_sizes(product):
                            messages.error(request, 'Choose a valid shoe size.')
                            return redirect('store:cart_detail')
                        cart_item['size'] = size_value
                    cart_data[product_id] = cart_item
                    _save_session_cart(request, cart_data)
        return redirect('store:cart_detail')

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_items = cart.items.select_related('product') if cart else []
        total = cart.total_price if cart else 0
        items = [
            {
                'item_id': item.pk,
                'product': item.product,
                'quantity': item.quantity,
                'size': item.size,
                'size_options': _product_sizes(item.product),
                'total_price': item.total_price,
            }
            for item in cart_items
        ]
    else:
        cart_data = request.session.get('cart', {})
        product_ids = [int(pid) for pid in cart_data.keys()]
        products = Product.objects.filter(id__in=product_ids)
        items = []
        total = 0
        prod_map = {p.id: p for p in products}
        for pid_str, value in cart_data.items():
            pid = int(pid_str)
            prod = prod_map.get(pid)
            if prod:
                cart_item = _session_cart_item(value)
                quantity = int(cart_item['quantity'])
                item = {
                    'product': prod,
                    'quantity': quantity,
                    'size': cart_item['size'],
                    'size_options': _product_sizes(prod),
                    'total_price': prod.price * quantity,
                }
                items.append(item)
                total += item['total_price']
    return render(
        request,
        'store/cart.html',
        {'items': items, 'total': total, 'quantity_options': range(1, 100)},
    )


def checkout(request):
    """Create an order for local test payment or a clearly marked demo checkout."""
    if request.method not in {'GET', 'POST'}:
        return HttpResponseNotAllowed(['GET', 'POST'])

    items, total = _get_checkout_items(request)
    if not items:
        return redirect('store:product_list')

    if request.method == 'GET':
        return render(
            request,
            'store/checkout.html',
            {
                'items': [
                    {
                        'product': product,
                        'quantity': quantity,
                        'size': size,
                        'line_total': product.price * quantity,
                    }
                    for product, quantity, size in items
                ],
                'total': total,
                'demo_payments_enabled': settings.DEBUG,
            },
        )

    payment_method = request.POST.get('payment_method', '')
    demo_payment_methods = {'google_pay', 'paypal', 'clearpay', 'klarna'}
    is_demo_checkout = payment_method in demo_payment_methods
    if payment_method and not is_demo_checkout:
        messages.error(request, 'Choose one of the listed demo payment options.')
        return redirect('store:checkout')
    if not settings.DEBUG and not is_demo_checkout:
        messages.error(request, 'Choose a demo checkout option to continue.')
        return redirect('store:checkout')

    shipping_address = request.POST.get('shipping_address', '').strip()
    billing_address = request.POST.get('billing_address', '').strip()
    if not shipping_address or not billing_address:
        messages.error(request, 'Enter both shipping and billing addresses.')
        return redirect('store:checkout')
    if len(shipping_address) > 255 or len(billing_address) > 255:
        messages.error(request, 'Addresses must be 255 characters or fewer.')
        return redirect('store:checkout')

    if not request.user.is_authenticated and request.session.session_key is None:
        request.session.create()
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        shipping_address=shipping_address,
        billing_address=billing_address,
        total_amount=total,
        paid=False,
        demo_payment_method=payment_method if is_demo_checkout else '',
        checkout_session_key=request.session.session_key or '',
    )
    for prod, qty, size in items:
        OrderItem.objects.create(
            order=order,
            product=prod,
            quantity=qty,
            size=size,
            price=prod.price,
        )
    if is_demo_checkout:
        _clear_order_items(order, request)
        return redirect('store:checkout_success', order_id=order.pk)
    return redirect('store:test_payment', order_id=order.pk)


def test_payment(request, order_id):
    if not settings.DEBUG:
        raise Http404
    order = get_object_or_404(Order, pk=order_id)
    if order.is_demo or not _order_belongs_to_request(order, request):
        raise Http404
    if request.method == 'POST':
        if not order.paid:
            order.paid = True
            order.save(update_fields=['paid'])
            _clear_order_items(order, request)
        return redirect('store:checkout_success', order_id=order.pk)
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET', 'POST'])
    return render(request, 'store/test_payment.html', {'order': order})


def checkout_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if not _order_belongs_to_request(order, request) or not (order.paid or order.is_demo):
        return redirect('store:cart_detail')
    return render(
        request,
        'store/checkout_success.html',
        {
            'order': order,
            'test_payment': settings.DEBUG and order.paid,
            'demo_order': order.is_demo,
        },
    )
