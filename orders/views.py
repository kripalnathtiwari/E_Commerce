from category.models import Category
from django.shortcuts import render, redirect
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required
from .models import Address, UploadedDesign, PrintOrder, Order, OrderItem
from .models import Product
from django.shortcuts import get_object_or_404
from store.models import Product as StoreProduct
from django.utils.text import slugify
import uuid
from store.models import Order as StoreOrder
from store.models import OrderItem as StoreOrderItem
from django.contrib import messages
from store.models import Variation

@login_required
def checkout(request, product_id):

    product = StoreProduct.objects.select_related('distributor').get(id=product_id)

    # If product has variations, redirect to product detail page to ensure selection
    if product.colors().exists() or product.sizes().exists():
        messages.info(request, "Please select color and size options.")
        return redirect('product_detail', product_id=product.id)

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":

        address_id = request.POST.get("address_id")
        
        # Variations from POST (if any were added in a custom way)
        product_variation = []
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

        # ---------- USE EXISTING ADDRESS ----------
        if address_id:
            address = Address.objects.get(id=address_id, user=request.user)

        # ---------- CREATE NEW ADDRESS ----------
        else:
            set_as_default = request.POST.get("set_as_default") == "on"
            is_first = not Address.objects.filter(user=request.user).exists()
            
            # If set as default or first address, clear existing defaults for this user
            if set_as_default or is_first:
                Address.objects.filter(user=request.user).update(is_default=False)

            address = Address.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                house=request.POST.get("house"),
                area=request.POST.get("area"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
                is_default=(set_as_default or is_first)
            )

        # ---------- DESIGN ----------
        design_img = request.FILES.get("design")

        design = None
        if design_img:
            design = UploadedDesign.objects.create(
                user=request.user,
                image=design_img
            )

        payment_method = request.POST.get("payment_method")
        
        if not payment_method:
             # Default to COD if not provided, or handle error
             payment_method = "cod"

        total_price = product.price if product.stock > 0 else 0

        # ---------- CREATE PRINT ORDER ----------
        order = PrintOrder.objects.create(
            user=request.user,
            product=product,
            design=design,
            address=address,
            distributor=product.distributor,
            payment_method=payment_method,
            quantity=1, # Defaulting to 1 for direct checkout
            total_price=total_price
        )
        if product_variation:
            order.variations.set(product_variation)
            order.save()

        # ---------- PAYMENT STATUS ----------
        if payment_method == "cod":
            order.payment_status = "cod_confirmed"

        elif payment_method == "qr":
            order.payment_status = "verification_pending"
            order.payment_proof = request.FILES.get("payment_proof")

        order.save()

        # ---------- CREATE STORE ORDER ----------
        store_order = StoreOrder.objects.create(
            user=request.user,
            total=total_price
        )

        store_order_item = StoreOrderItem.objects.create(
            order=store_order,
            product=product,
            distributor=order.distributor,
            quantity=1, # Defaulting to 1 for direct checkout, can be enhanced if needed
            price=total_price
        )
        if product_variation:
            store_order_item.variations.set(product_variation)
            store_order_item.save()

        return redirect("/")

    return render(request, "store/checkout.html", {
        "product": product,
        "addresses": addresses
    })

@login_required
def distributor_dashboard(request):
    return redirect('distributor_orders')

@login_required
def place_order(request, product_id):
    product = Product.objects.get(id=product_id)
    
    # If product has variations, redirect to product detail page to ensure selection
    from store.models import Product as StoreProduct
    store_p = StoreProduct.objects.get(id=product_id)
    if store_p.colors().exists() or store_p.sizes().exists():
        messages.info(request, "Please select color and size options.")
        return redirect('product_detail', product_id=product_id)

    distributor = product.distributor

    order = Order.objects.create(
        user=request.user,
        distributor=product.distributor,
        address="User Address Here",
        total_price=product.price,
        payment_status='paid'
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        distributor=distributor,
        quantity=1,
        price=product.price
    )

    return redirect('user_orders')

# Removed duplicate distributor_orders function

@login_required
def update_delivery_status(request, order_id):

    distributor = request.user.distributor_profile
    status = request.POST.get('status')
    
    # Try updating Standard Order
    try:
        order = Order.objects.get(id=order_id, distributor=distributor)
        order.delivery_status = status
        order.save()
    except Order.DoesNotExist:
        # Try updating Print Order
        try:
            print_order = PrintOrder.objects.get(id=order_id, distributor=distributor)
            print_order.delivery_status = status
            print_order.save()
        except PrintOrder.DoesNotExist:
            pass # Or handle error

    return redirect('distributor_orders')

@login_required
def user_orders(request):

    orders = Order.objects.filter(user=request.user)

    return render(request,'user/orders.html',{'orders':orders})




@login_required
def add_product(request):

    distributor = request.user.distributor_profile
    categories = Category.objects.all()

    if request.method == "POST":

        name = request.POST.get('name')
        selected_category_id = request.POST.get('category')
        new_category_name = request.POST.get('new_category')
        new_category_image = request.FILES.get('new_category_image')

        # ---------- CREATE NEW CATEGORY ----------
        if new_category_name:
            category, created = Category.objects.get_or_create(
                category_name=new_category_name,
                defaults={
                    "slug": slugify(new_category_name),
                    "cat_image": new_category_image
                }
            )
        else:
            category = Category.objects.get(id=selected_category_id)

        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = int(request.POST.get('stock'))
        image = request.FILES.get('image')
        colors = request.POST.get('colors')
        sizes = request.POST.get('sizes')

        # ---------- CHECK IF PRODUCT ALREADY EXISTS ----------
        product = Product.objects.filter(
            distributor=distributor,
            product_name=name
        ).first()

        if product:
            # Update existing product
            product.stock += int(stock)
            product.price = price
            product.description = description
            product.category = category

            if image:
                product.image = image

            product.save()

        else:
            # Create new product
            product = Product.objects.create(
                distributor=distributor,
                product_name=name,
                slug=slugify(name) + "-" + str(uuid.uuid4())[:6],
                description=description,
                price=price,
                stock=stock,
                category=category,
                image=image
            )

        # ---------- SAVE VARIATIONS ----------
        def save_variations(prod, category, values_str):
            if values_str:
                vals = [v.strip() for v in values_str.split(',') if v.strip()]
                for v_val in vals:
                    Variation.objects.get_or_create(
                        product=prod,
                        variation_category=category,
                        variation_value=v_val,
                        is_active=True
                    )

        save_variations(product, 'color', colors)
        save_variations(product, 'size', sizes)

        return redirect('distributor_dashboard')


    return render(request, 'distributor/add_product.html', {
        'categories': categories
    })

@login_required
def distributor_orders(request):

    distributor = request.user.distributor_profile
    
    # Fetch Standard Orders
    orders = Order.objects.filter(distributor=distributor).annotate(
        order_date=TruncDate('created_at')
    ).order_by('-created_at')
    
    # Fetch Print/Custom Orders
    print_orders = PrintOrder.objects.filter(distributor=distributor).annotate(
        order_date=TruncDate('created_at')
    ).order_by('-created_at')

    return render(request, 'distributor/orders.html', {
        'orders': orders,
        'print_orders': print_orders
    })

@login_required
def shop(request):
    from store.models import Product

    distributor_products = Product.objects.filter(distributor__isnull=False)

    distributor = None
    if hasattr(request.user, 'distributor_profile'):
        distributor = request.user.distributor_profile

    return render(request, 'store/store.html', {
        'products': distributor_products,
        'distributor': distributor
    })
@login_required
def buy_product(request, product_id):
    product = Product.objects.get(id=product_id)
    
    # If product has variations, redirect to product detail page to ensure selection
    from store.models import Product as StoreProduct
    store_p = StoreProduct.objects.get(id=product_id)
    if store_p.colors().exists() or store_p.sizes().exists():
        messages.info(request, "Please select color and size options.")
        return redirect('product_detail', product_id=product_id)

    distributor = product.distributor

    order = Order.objects.create(
        user=request.user,
        distributor=product.distributor,
        address="Default Address",  # later we add form
        total_price=product.price,
        payment_status='paid'
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        distributor=distributor,
        quantity=1,
        price=product.price
    )

    return redirect('user_orders')

@login_required
def user_orders(request):

    orders = Order.objects.filter(user=request.user)

    return render(request, 'shop/my_orders.html', {'orders': orders})

@login_required
def distributor_products(request):
    distributor = request.user.distributor_profile
    products = StoreProduct.objects.filter(distributor=distributor)

    return render(request, "distributor/products.html", {"products": products})

@login_required
def update_stock(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(StoreProduct, id=product_id, distributor=request.user.distributor_profile)
        action = request.POST.get('action')
        new_stock = request.POST.get('stock')

        if action == "increase":
            product.stock += 1
        elif action == "decrease":
            if product.stock > 0:
                product.stock -= 1
        elif new_stock is not None:
            try:
                product.stock = max(0, int(new_stock))
            except ValueError:
                pass
            
        product.save()
        
    return redirect(request.META.get('HTTP_REFERER', 'shop'))