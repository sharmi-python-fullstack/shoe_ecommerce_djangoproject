from django.db.models import Sum

from .models import CartItem


SHOP_MENUS = [
    {
        'label': 'Womens',
        'category': 'women',
        'columns': [
            ('New Arrivals', ['View all']),
            ('Sandals', ['Flat', 'Flip Flop', 'Slider', 'Strappy']),
            ('Trainers', ['Chunky', 'Lace Up', 'Slip On']),
            ('Canvas', ['Lace Up', 'Slip On']),
            ('Shoes', ['Ballerina', 'Brogue', 'Flat', 'Heel', 'Leather', 'Party', 'School']),
            ('Safety Footwear', ['Boots', 'Shoes', 'Steel toe cap', 'Trainers']),
            ('Boots', ['Ankle', 'Biker', 'Heel', 'Knee High', 'Lace up', 'Leather']),
            ('Slippers', ['Easy Fasten', 'Full', 'Moccasin', 'Mule', 'Slipper Boots']),
        ],
    },
    {
        'label': 'Mens',
        'category': 'men',
        'columns': [
            ('New Arrivals', ['View all']),
            ('Sandals', ['Flip Flop', 'Mule', 'Slider', 'Sport']),
            ('Trainers', ['Easy Fasten', 'Lace Up', 'Slip On']),
            ('Canvas', ['Lace Up', 'Slip On']),
            ('Shoes', ['Brogue', 'Casual', 'Easy Fasten', 'Lace up', 'Leather', 'Loafer', 'Oxford']),
            ('Safety Footwear', ['Boots', 'Shoes', 'Steel toe cap', 'Trainers']),
            ('Boots', ['Ankle', 'Chelsea', 'Desert', 'Lace up', 'Leather', 'Pull on']),
            ('Slippers', ['Full', 'Moccasin', 'Mule']),
        ],
    },
    {
        'label': 'Kids',
        'category': 'kids',
        'columns': [
            ('New Arrivals', ['View all']),
            ('Girls', ['Sandals', 'Shoes', 'Trainers', 'Boots']),
            ('Boys', ['Sandals', 'Shoes', 'Trainers', 'Boots']),
            ('Brands', ['Barbie', 'Disney', 'Paw Patrol', 'Pokemon', 'Skechers']),
            ('School', ['Shoes', 'Trainers']),
            ('Slippers', ['Clogs', 'Flip Flops', 'Slippers']),
        ],
    },
    {
        'label': 'Brands',
        'category': '',
        'columns': [
            ('B - C', ['Barbie', 'Beckett', 'Bluey', 'Comfort Plus', 'Comfy Steps', 'Crocs']),
            ('D - G', ['Disney Frozen', 'Disney Stitch', 'Dunlop', 'EarthWorks', 'Gabbys Dollhouse']),
            ('H - J', ['Heart', 'Heavenly Feet', 'Hobos', 'Hush Puppies', 'Jo & Joe', 'JuJu']),
            ('K - L', ['Kickers', 'Krush', 'Lambretta', 'Lilley', 'LoL', 'Lotus', 'Lunar']),
            ('M - O', ['Marco Lozzi', 'Marvel', 'Maya Grace', 'Original Penguin', 'Osaga']),
            ('P - R', ['Paw Patrol', 'Pokemon', 'Red Fish', 'Red Level', 'Regatta', 'Rieker', 'Rocket Dog']),
            ('S - W', ['Skechers', 'Soft Line', 'Spider-Man', 'Super Mario', 'Trespass', 'Umbro', 'Walkright']),
        ],
    },
    {
        'label': 'Offers',
        'category': '',
        'columns': [
            ('Offers', ['Save', 'Two pairs for a thousand', 'Clearance Outlet', 'Boots Sale']),
            ('Featured', ['First order gift', '50% offer', 'View all offers']),
        ],
    },
]


def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(cart__user=request.user).aggregate(
            total=Sum('quantity')
        )['total']
        return {'cart_count': count or 0, 'shop_menus': SHOP_MENUS}

    cart = request.session.get('cart', {})
    return {
        'cart_count': sum(
            int(value.get('quantity', 1) if isinstance(value, dict) else value)
            for value in cart.values()
        ),
        'shop_menus': SHOP_MENUS,
    }
