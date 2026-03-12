import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from store.models import Product, Variation

with open("debug_results.txt", "w") as f:
    f.write(f"Total Variations: {Variation.objects.count()}\n")
    for v in Variation.objects.all():
        f.write(f"Product: {v.product.product_name}, Cat: {v.variation_category}, Val: {v.variation_value}\n")
    
    p = Product.objects.filter(id=9).first()
    if p:
        f.write(f"Product 9 colors: {list(p.colors())}\n")
        f.write(f"Product 9 sizes: {list(p.sizes())}\n")
