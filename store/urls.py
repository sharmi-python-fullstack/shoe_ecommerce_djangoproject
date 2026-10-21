from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('account/', views.account, name='account'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/razorpay/<int:order_id>/', views.razorpay_payment, name='razorpay_payment'),
    path(
        'checkout/razorpay/<int:order_id>/verify/',
        views.verify_razorpay_payment,
        name='verify_razorpay_payment',
    ),
    path('checkout/test-payment/<int:order_id>/', views.test_payment, name='test_payment'),
    path('checkout/success/<int:order_id>/', views.checkout_success, name='checkout_success'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
