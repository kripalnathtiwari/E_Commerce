import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from store.models import Product, Variation

def check_data():
    products = Product.objects.all()
    print(f"Total Products: {products.count()}")
    for p in products:
        print(f"Product: {p.product_name} (ID: {p.id})")
        variations = Variation.objects.filter(product=p)
        print(f"  Variations found: {variations.count()}")
        for v in variations:
            print(f"    - {v.variation_category}: {v.variation_value}")

if __name__ == "__main__":
    check_data()
