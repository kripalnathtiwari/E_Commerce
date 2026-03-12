import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from store.models import Product, Variation

try:
    p = Product.objects.get(id=9)
    print(f"Product: {p.product_name}")
    print(f"Colors: {list(p.colors())}")
    print(f"Sizes: {list(p.sizes())}")
    
    all_vars = Variation.objects.filter(product=p)
    print(f"All variations for product 9: {list(all_vars)}")
    
except Product.DoesNotExist:
    print("Product 9 not found")
except Exception as e:
    print(f"Error: {e}")
