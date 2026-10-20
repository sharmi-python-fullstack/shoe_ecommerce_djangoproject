from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Cart,
    CartItem,
    ContactInquiry,
    NewsletterSubscription,
    Order,
    OrderItem,
    Product,
)


class ProductListTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Everyday Runner',
            slug='everyday-runner',
            description='A comfortable everyday shoe',
            price='2999.00',
        )

    def test_homepage_renders_storefront_and_admin_login(self):
        response = self.client.get(reverse('store:product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'StepUp.in')
        self.assertContains(response, 'What are you looking for?')
        self.assertContains(response, self.product.name)
        self.assertContains(response, reverse('store:account'))
        self.assertNotContains(response, reverse('admin:login'))

    def test_product_images_can_be_opened_in_zoom_viewer(self):
        catalogue_response = self.client.get(reverse('store:product_list'))
        detail_response = self.client.get(
            reverse('store:product_detail', args=[self.product.slug])
        )

        self.assertContains(catalogue_response, 'data-image-zoom')
        self.assertContains(detail_response, 'data-image-zoom')
        self.assertContains(detail_response, 'data-zoom-in')
        self.assertContains(detail_response, 'data-zoom-out')
        self.assertContains(detail_response, 'data-zoom-reset')

    def test_bundled_product_images_use_distinct_static_urls(self):
        first = Product.objects.create(
            name='Boat Shoe',
            slug='boat-shoe',
            price='1000.00',
            image='products/harlan-mens-tan-boat-shoe.png',
        )
        second = Product.objects.create(
            name='Black Loafer',
            slug='black-loafer',
            price='1200.00',
            image='products/kingsley-mens-black-loafer.png',
        )

        catalogue_response = self.client.get(reverse('store:product_list'))
        detail_response = self.client.get(
            reverse('store:product_detail', args=[first.slug])
        )
        self.client.get(reverse('store:add_to_cart', args=[first.id]))
        cart_response = self.client.get(reverse('store:cart_detail'))

        self.assertContains(
            catalogue_response,
            f'/static/images/products/{first.image.name.rsplit("/", 1)[-1]}',
        )
        self.assertContains(
            catalogue_response,
            f'/static/images/products/{second.image.name.rsplit("/", 1)[-1]}',
        )
        self.assertContains(
            detail_response,
            f'/static/images/products/{first.image.name.rsplit("/", 1)[-1]}',
        )
        self.assertContains(
            cart_response,
            f'/static/images/products/{first.image.name.rsplit("/", 1)[-1]}',
        )
        self.assertNotEqual(first.display_image_url, second.display_image_url)

    def test_search_filters_products_by_name_and_description(self):
        Product.objects.create(
            name='Classic Sandal',
            slug='classic-sandal',
            description='A leather sandal for summer',
            price='1499.00',
        )

        response = self.client.get(reverse('store:product_list'), {'q': 'leather'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Classic Sandal')
        self.assertNotContains(response, self.product.name)

    def test_category_and_style_filters_are_applied(self):
        self.product.category = 'women'
        self.product.save()
        Product.objects.create(
            name='Classic Sandal',
            slug='classic-sandal',
            description='A leather sandal for summer',
            price='1499.00',
            category='kids',
        )

        response = self.client.get(
            reverse('store:product_list'),
            {'category': 'women', 'style': 'runner'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, 'Classic Sandal')

    def test_each_category_filter_only_shows_products_in_that_category(self):
        self.product.category = 'women'
        self.product.save()
        mens_product = Product.objects.create(
            name='Everyday Mens Trainer',
            slug='everyday-mens-trainer',
            description='A comfortable mens trainer',
            price='2499.00',
            category='men',
        )
        kids_product = Product.objects.create(
            name='Kids Canvas Shoe',
            slug='kids-canvas-shoe',
            description='A canvas shoe for kids',
            price='1499.00',
            category='kids',
        )

        for category, expected, excluded in [
            ('women', self.product.name, [mens_product.name, kids_product.name]),
            ('men', mens_product.name, [self.product.name, kids_product.name]),
            ('kids', kids_product.name, [self.product.name, mens_product.name]),
        ]:
            with self.subTest(category=category):
                response = self.client.get(
                    reverse('store:product_list'),
                    {'category': category},
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)
                for product_name in excluded:
                    self.assertNotContains(response, product_name)

    def test_homepage_contains_carousels_mega_menus_and_supplied_gallery(self):
        response = self.client.get(reverse('store:product_list'))

        self.assertContains(response, 'data-carousel')
        self.assertContains(response, 'Flat 50% Sale')
        self.assertContains(response, 'Womens High Heels')
        self.assertContains(response, 'Mens wear high heel office shoe')
        self.assertContains(response, 'Womens red color high heel for party')
        self.assertContains(response, 'New Arrivals')
        self.assertContains(response, 'image-43.png')
        self.assertContains(response, 'Overview')

    def test_newsletter_subscription_is_saved_and_deduplicated(self):
        url = reverse('store:newsletter_subscribe')

        first_response = self.client.post(url, {'email': 'Style@Example.com'})
        second_response = self.client.post(url, {'email': 'style@example.com'})

        self.assertRedirects(first_response, reverse('store:product_list'))
        self.assertRedirects(second_response, reverse('store:product_list'))
        self.assertEqual(
            NewsletterSubscription.objects.filter(email='style@example.com').count(),
            1,
        )

    def test_newsletter_rejects_invalid_email(self):
        response = self.client.post(
            reverse('store:newsletter_subscribe'),
            {'email': 'not-an-email'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid email address')
        self.assertEqual(NewsletterSubscription.objects.count(), 0)

    def test_admin_product_list_requires_login(self):
        response = self.client.get(reverse('admin:store_product_changelist'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response['Location'])

    def test_primary_navigation_links_to_storefront_pages(self):
        response = self.client.get(reverse('store:product_list'))

        self.assertContains(response, f'href="{reverse("store:about")}"')
        self.assertContains(response, f'href="{reverse("store:contact")}"')
        self.assertContains(response, f'href="{reverse("store:account")}"')
        self.assertContains(response, f'href="{reverse("store:cart_detail")}"')
        for category in ('women', 'men', 'kids'):
            self.assertContains(
                response,
                f'data-category-url="/?category={category}#products"',
            )

    def test_about_and_contact_pages_render_and_contact_form_saves_inquiry(self):
        about_response = self.client.get(reverse('store:about'))
        contact_response = self.client.get(reverse('store:contact'))

        self.assertEqual(about_response.status_code, 200)
        self.assertContains(about_response, 'Our Mission')
        self.assertEqual(contact_response.status_code, 200)
        self.assertContains(contact_response, 'Enquiry Form')

        submit_response = self.client.post(
            reverse('store:contact'),
            {
                'name': 'A StepUp customer',
                'email': 'CUSTOMER@example.com',
                'phone': '9976357250',
                'message': 'I need help with an order.',
            },
        )

        self.assertRedirects(submit_response, reverse('store:contact'))
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.email, 'customer@example.com')
        self.assertEqual(inquiry.name, 'A StepUp customer')

    def test_customer_registration_and_login_use_storefront_account(self):
        registration_response = self.client.post(
            reverse('store:account'),
            {
                'mode': 'register',
                'email': 'customer@example.com',
                'password': 'Shoe-store-Strong-482!',
                'password_confirm': 'Shoe-store-Strong-482!',
            },
        )

        self.assertRedirects(registration_response, reverse('store:product_list'))
        user = get_user_model().objects.get(email='customer@example.com')
        self.assertTrue(user.is_authenticated)
        self.client.logout()

        login_response = self.client.post(
            reverse('store:account'),
            {
                'mode': 'login',
                'email': 'customer@example.com',
                'password': 'Shoe-store-Strong-482!',
            },
        )

        self.assertRedirects(login_response, reverse('store:product_list'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_account_page_keeps_separate_admin_login_link(self):
        response = self.client.get(reverse('store:account'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('admin:login'))

    def test_anonymous_cart_quantity_can_be_updated_and_item_removed(self):
        session = self.client.session
        session['cart'] = {str(self.product.id): 1}
        session.save()

        update_response = self.client.post(
            reverse('store:cart_detail'),
            {'action': 'update', 'product_id': self.product.id, 'quantity': 3},
        )

        self.assertRedirects(update_response, reverse('store:cart_detail'))
        self.assertEqual(
            self.client.session['cart'][str(self.product.id)],
            {'quantity': 3, 'size': ''},
        )

        remove_response = self.client.post(
            reverse('store:cart_detail'),
            {'action': 'remove', 'product_id': self.product.id},
        )

        self.assertRedirects(remove_response, reverse('store:cart_detail'))
        self.assertEqual(self.client.session['cart'], {})

    def test_cart_links_to_local_test_checkout(self):
        self.client.post(reverse('store:add_to_cart', args=[self.product.id]))

        response = self.client.get(reverse('store:cart_detail'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Free &amp; Fast arriving by Monday')
        self.assertContains(response, 'Size (41)')
        self.assertContains(response, 'Quantity (1)')
        self.assertContains(response, 'Test checkout')
        self.assertContains(response, 'simulate checkout with no real payment')

    def test_checkout_offers_demo_express_payment_choices(self):
        self.client.post(reverse('store:add_to_cart', args=[self.product.id]))

        response = self.client.get(reverse('store:checkout'))

        self.assertContains(response, 'Express checkout')
        self.assertContains(response, 'Google Pay')
        self.assertContains(response, 'PayPal')
        self.assertContains(response, 'Clearpay')
        self.assertContains(response, 'Klarna')
        self.assertContains(response, 'visual examples, not connected')

    def test_selected_size_is_saved_for_anonymous_cart_and_order(self):
        self.client.post(reverse('store:add_to_cart', args=[self.product.id]))

        update_response = self.client.post(
            reverse('store:cart_detail'),
            {
                'action': 'update',
                'product_id': self.product.id,
                'quantity': 2,
                'size': '42',
            },
        )

        self.assertRedirects(update_response, reverse('store:cart_detail'))
        self.assertEqual(
            self.client.session['cart'][str(self.product.id)],
            {'quantity': 2, 'size': '42'},
        )

        response = self.client.get(reverse('store:checkout'))
        self.assertContains(response, 'Everyday Runner × 2 (size 42)')
        self.assertFalse(Order.objects.exists())

    def test_cart_rejects_size_outside_product_category_range(self):
        self.product.category = 'kids'
        self.product.save()
        self.client.post(reverse('store:add_to_cart', args=[self.product.id]))

        response = self.client.post(
            reverse('store:cart_detail'),
            {
                'action': 'update',
                'product_id': self.product.id,
                'quantity': 1,
                'size': '41',
            },
            follow=True,
        )

        self.assertContains(response, 'Choose a valid shoe size.')
        self.assertEqual(
            self.client.session['cart'][str(self.product.id)],
            {'quantity': 1, 'size': '30'},
        )

    def test_authenticated_cart_quantity_can_be_updated_and_item_removed(self):
        user = get_user_model().objects.create_user(
            username='cart-shopper',
            password='test-password',
        )
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, product=self.product, size='41')
        self.client.force_login(user)

        update_response = self.client.post(
            reverse('store:cart_detail'),
            {'action': 'update', 'item_id': item.pk, 'quantity': 4, 'size': '42'},
        )

        self.assertRedirects(update_response, reverse('store:cart_detail'))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)
        self.assertEqual(item.size, '42')

        remove_response = self.client.post(
            reverse('store:cart_detail'),
            {'action': 'remove', 'item_id': item.pk},
        )

        self.assertRedirects(remove_response, reverse('store:cart_detail'))
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    @override_settings(DEBUG=True)
    def test_authenticated_checkout_creates_order_and_test_payment_confirms_it(self):
        user = get_user_model().objects.create_user(
            username='shopper',
            password='test-password',
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_login(user)

        checkout_response = self.client.post(
            reverse('store:checkout'),
            {
                'shipping_address': '1 Shoe Street, Mumbai',
                'billing_address': '1 Shoe Street, Mumbai',
            },
        )

        order = Order.objects.get(user=user)
        self.assertRedirects(
            checkout_response,
            reverse('store:test_payment', args=[order.pk]),
        )
        self.assertFalse(order.paid)
        self.assertEqual(order.shipping_address, '1 Shoe Street, Mumbai')
        self.assertEqual(order.total_amount, Decimal('5998.00'))
        self.assertTrue(cart.items.exists())
        self.assertEqual(OrderItem.objects.get(order=order).quantity, 2)

        payment_page = self.client.get(reverse('store:test_payment', args=[order.pk]))
        self.assertContains(payment_page, 'This is a local test page')
        self.assertContains(payment_page, 'Simulate successful payment')
        self.assertContains(payment_page, '₹ 5,998.00')

        payment_response = self.client.post(reverse('store:test_payment', args=[order.pk]))
        self.assertRedirects(
            payment_response,
            reverse('store:checkout_success', args=[order.pk]),
        )
        order.refresh_from_db()
        self.assertTrue(order.paid)
        self.assertFalse(cart.items.exists())
        success_response = self.client.get(reverse('store:checkout_success', args=[order.pk]))
        self.assertContains(success_response, '🙂 Your order was placed!')
        self.assertContains(success_response, 'No money was taken.')

    @override_settings(DEBUG=True)
    def test_anonymous_checkout_uses_session_cart_and_retains_cart_until_test_success(self):
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session.save()

        checkout_response = self.client.post(
            reverse('store:checkout'),
            {'shipping_address': 'Shipping', 'billing_address': 'Billing'},
        )

        order = Order.objects.get(user=None)
        self.assertRedirects(
            checkout_response,
            reverse('store:test_payment', args=[order.pk]),
        )
        self.assertEqual(self.client.session['cart'], {str(self.product.id): 2})
        payment_response = self.client.post(reverse('store:test_payment', args=[order.pk]))
        self.assertRedirects(
            payment_response,
            reverse('store:checkout_success', args=[order.pk]),
        )
        self.assertEqual(self.client.session['cart'], {})
        order.refresh_from_db()
        self.assertTrue(order.paid)

    @override_settings(DEBUG=False)
    def test_demo_payment_is_disabled_outside_debug_mode(self):
        self.client.post(reverse('store:add_to_cart', args=[self.product.id]))
        checkout_response = self.client.get(reverse('store:checkout'))
        self.assertEqual(checkout_response.status_code, 200)
        self.assertContains(checkout_response, 'Demo payments are disabled on this live site.')
        self.assertContains(checkout_response, '<button class="express-payment-button express-google-pay" type="submit" disabled>')

        session = self.client.session
        session['cart'] = {str(self.product.id): 1}
        session.save()
        response = self.client.post(
            reverse('store:checkout'),
            {'shipping_address': 'Shipping', 'billing_address': 'Billing'},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Order.objects.exists())


class SeedDemoProductsCommandTests(TestCase):
    def test_seeds_an_empty_catalogue_once_without_overwriting_products(self):
        call_command('seed_demo_products', stdout=StringIO())

        self.assertEqual(Product.objects.count(), 22)
        product = Product.objects.get(slug='ophelia-womens-silver-diamante-heel')
        product.price = Decimal('1.00')
        product.save()

        call_command('seed_demo_products', stdout=StringIO())

        self.assertEqual(Product.objects.count(), 22)
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal('1.00'))
