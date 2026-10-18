from decimal import Decimal
from django.core.management.base import BaseCommand
from restaurants.models import Restaurant
from menu.models import Category, MenuItem


class Command(BaseCommand):
    help = 'Seeds pilot restaurant data for TapBhoj'

    def handle(self, *args, **options):
        # Create or update Pilot Restaurant
        restaurant, created = Restaurant.objects.update_or_create(
            slug='dilli-rasoi',
            defaults={
                'name': 'Dilli Rasoi',
                'description': 'Authentic North Indian curries, kebabs, and fresh breads.',
                'whatsapp_number': '919876543210',
                'address': 'Plot 42, Connaught Circle, New Delhi',
                'google_review_url': 'https://g.page/r/dilli-rasoi/review',
                'number_of_tables': 12,
                'status': 'active',
            }
        )

        # Clear existing menu items and categories for a clean seed
        restaurant.categories.all().delete()

        # Categories & Items
        menu_data = [
            {
                'category': 'Starters & Kebabs',
                'items': [
                    {
                        'name': 'Paneer Tikka',
                        'description': 'Char-grilled cottage cheese cubes marinated in spiced yogurt and kasuri methi.',
                        'price': Decimal('260.00'),
                        'is_veg': True,
                        'tags': 'Bestseller',
                        'is_available': True,
                    },
                    {
                        'name': 'Dahi Ke Kebab',
                        'description': 'Crispy golden patties of hung curd, cardamom, and fresh coriander.',
                        'price': Decimal('240.00'),
                        'is_veg': True,
                        'tags': "Chef's Pick",
                        'is_available': True,
                    },
                    {
                        'name': 'Chicken Malai Tikka',
                        'description': 'Tender boneless chicken marinated in cream, cheese, and crushed green cardamom.',
                        'price': Decimal('320.00'),
                        'is_veg': False,
                        'tags': 'Bestseller',
                        'is_available': True,
                    },
                    {
                        'name': 'Mutton Seekh Kebab',
                        'description': 'Minced spiced lamb skewered and roasted in clay oven.',
                        'price': Decimal('380.00'),
                        'is_veg': False,
                        'tags': '',
                        'is_available': False,  # Sold out test item
                    },
                ]
            },
            {
                'category': 'Main Course Curries',
                'items': [
                    {
                        'name': 'Dal Makhani',
                        'description': 'Slow-cooked black lentils simmered overnight with cream and churned butter.',
                        'price': Decimal('280.00'),
                        'is_veg': True,
                        'tags': 'Bestseller',
                        'is_available': True,
                    },
                    {
                        'name': 'Paneer Butter Masala',
                        'description': 'Cottage cheese simmered in rich tomato gravy with butter and aromatic herbs.',
                        'price': Decimal('310.00'),
                        'is_veg': True,
                        'tags': '',
                        'is_available': True,
                    },
                    {
                        'name': 'Butter Chicken (Murgh Makhani)',
                        'description': 'Tandoori chicken pieces in creamy, mildly sweet and savory tomato satin gravy.',
                        'price': Decimal('390.00'),
                        'is_veg': False,
                        'tags': 'Bestseller',
                        'is_available': True,
                    },
                    {
                        'name': 'Rara Gosht',
                        'description': 'Mutton pieces cooked in thick minced lamb gravy with whole spices.',
                        'price': Decimal('450.00'),
                        'is_veg': False,
                        'tags': "Chef's Pick",
                        'is_available': True,
                    },
                ]
            },
            {
                'category': 'Fresh Tandoori Breads',
                'items': [
                    {
                        'name': 'Butter Naan',
                        'description': 'Soft refined flour bread baked in clay tandoor and brushed with butter.',
                        'price': Decimal('55.00'),
                        'is_veg': True,
                        'tags': '',
                        'is_available': True,
                    },
                    {
                        'name': 'Garlic Naan',
                        'description': 'Crispy naan topped with minced roasted garlic and fresh coriander.',
                        'price': Decimal('75.00'),
                        'is_veg': True,
                        'tags': 'Popular',
                        'is_available': True,
                    },
                    {
                        'name': 'Tandoori Roti',
                        'description': 'Traditional whole wheat flatbread baked in the tandoor.',
                        'price': Decimal('30.00'),
                        'is_veg': True,
                        'tags': '',
                        'is_available': True,
                    },
                ]
            },
            {
                'category': 'Beverages & Desserts',
                'items': [
                    {
                        'name': 'Special Masala Chaas',
                        'description': 'Chilled spiced buttermilk tempered with roasted cumin and mint.',
                        'price': Decimal('70.00'),
                        'is_veg': True,
                        'tags': '',
                        'is_available': True,
                    },
                    {
                        'name': 'Gulab Jamun (2 pcs)',
                        'description': 'Warm khoya dumplings steeped in rose and saffron syrup.',
                        'price': Decimal('110.00'),
                        'is_veg': True,
                        'tags': 'Sweet Tooth',
                        'is_available': True,
                    },
                ]
            },
        ]

        for cat_pos, cat_data in enumerate(menu_data, start=1):
            category = Category.objects.create(
                restaurant=restaurant,
                name=cat_data['category'],
                position=cat_pos,
                is_visible=True,
            )
            for item_pos, item in enumerate(cat_data['items'], start=1):
                MenuItem.objects.create(
                    restaurant=restaurant,
                    category=category,
                    name=item['name'],
                    description=item['description'],
                    price=item['price'],
                    is_veg=item['is_veg'],
                    tags=item['tags'],
                    is_available=item['is_available'],
                    position=item_pos,
                )

        # Also create a paused restaurant for verification of C9
        chai_restaurant, _ = Restaurant.objects.update_or_create(
            slug='chai-shai',
            defaults={
                'name': 'Chai Shai Cafe',
                'description': 'Artisanal teas and cafe bites.',
                'whatsapp_number': '919876543211',
                'status': 'paused',
                'number_of_tables': 6,
            }
        )

        # Create or update Owner Users for Testing
        from django.contrib.auth.models import User
        from accounts.models import OwnerProfile

        # Owner 1 (Dilli Rasoi)
        owner_user, _ = User.objects.update_or_create(
            username='owner',
            defaults={'email': 'owner@dillirasoi.com', 'is_staff': False}
        )
        owner_user.set_password('Password@123')
        owner_user.save()
        OwnerProfile.objects.update_or_create(
            user=owner_user,
            defaults={'restaurant': restaurant}
        )

        # Owner 2 (Chai Shai Cafe - for tenant isolation testing)
        owner_user2, _ = User.objects.update_or_create(
            username='owner2',
            defaults={'email': 'owner@chaishai.com', 'is_staff': False}
        )
        owner_user2.set_password('Password@123')
        owner_user2.save()
        OwnerProfile.objects.update_or_create(
            user=owner_user2,
            defaults={'restaurant': chai_restaurant}
        )

        self.stdout.write(self.style.SUCCESS(
            'Successfully seeded pilot data and owners:\n'
            '  Owner 1: username=owner, password=Password@123 (Dilli Rasoi)\n'
            '  Owner 2: username=owner2, password=Password@123 (Chai Shai Cafe)'
        ))
