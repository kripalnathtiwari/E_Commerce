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
from store.models import ProductImage
from django.core.mail import send_mail
from django.conf import settings

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

        elif payment_method == "card":
            order.payment_status = "paid"
            order.card_number = request.POST.get("card_number") # Just for simulation if needed
            order.expiry_date = request.POST.get("expiry_date")
            order.cvv = request.POST.get("cvv")

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

        # ---------- LINK PRINT ORDER TO STORE ORDER ITEM ----------
        order.store_order_item = store_order_item
        order.save()

        # ---------- SEND EMAIL ----------
        try:
            subject = f"Order Placed Successfully - Order #{store_order.id}"
            body = f"Hi {request.user.username},\n\nYour order has been placed successfully!\nOrder ID: #{store_order.id}\nTotal Amount: ₹{total_price}\n\nThank you for shopping with us!"
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True
            )
        except:
            pass

        messages.success(request, "🎉 Order placed successfully!")
        return redirect('store')

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

    from store.models import Order as StoreOrder, OrderItem as StoreOrderItem
    
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

    # Sync with store app for returns to work
    store_order = StoreOrder.objects.create(
        user=request.user,
        total=product.price
    )
    
    StoreOrderItem.objects.create(
        order=store_order,
        product=store_p,
        distributor=distributor,
        quantity=1,
        price=product.price,
        status='Pending'
    )

    return redirect('user_orders')

# Removed duplicate distributor_orders function

@login_required
def update_delivery_status(request, order_id):

    distributor = request.user.distributor_profile
    status = request.POST.get('status')
    
    status_map = {
        'pending': 'Pending',
        'assigned': 'Confirmed',
        'confirmed': 'Confirmed',
        'shipped': 'Shipped',
        'delivered': 'Delivered'
    }

    # Try updating Standard Order
    try:
        order = Order.objects.get(id=order_id, distributor=distributor)
        order.delivery_status = status
        order.save()
        
        # Sync to Store OrderItem
        from store.models import OrderItem as StoreOrderItem
        # Find matching item by order user, product etc
        # Since orders.models.Order can have multiple items, we update all matching ones
        items = OrderItem.objects.filter(order=order)
        for itm in items:
            store_item = StoreOrderItem.objects.filter(
                order__user=order.user,
                product=itm.product,
                quantity=itm.quantity,
                price=itm.price
            ).last()
            if store_item:
                store_item.status = status_map.get(status, 'Pending')
                store_item.save()

    except Order.DoesNotExist:
        # Try updating Print Order
        try:
            print_order = PrintOrder.objects.get(id=order_id, distributor=distributor)
            print_order.delivery_status = status
            print_order.save()
            
            # Sync to Store OrderItem if linked or find a match
            store_item = None
            if print_order.store_order_item:
                store_item = print_order.store_order_item
            else:
                # Fallback: Find matching StoreOrderItem by user, product, and quantity
                from store.models import OrderItem as StoreOrderItem
                store_item = StoreOrderItem.objects.filter(
                    order__user=print_order.user,
                    product=print_order.product,
                    quantity=print_order.quantity
                ).last()
                if store_item:
                    # Link it for future updates
                    print_order.store_order_item = store_item
                    print_order.save()

            if store_item:
                store_item.status = status_map.get(status, 'Pending')
                store_item.save()
                
        except PrintOrder.DoesNotExist:
            pass # Or handle error

    return redirect('distributor_orders')

@login_required
def update_payment_status(request, order_id):

    distributor = request.user.distributor_profile
    status = request.POST.get('payment_status')
    
    # Try updating Standard Order
    try:
        order = Order.objects.get(id=order_id, distributor=distributor)
        order.payment_status = status
        order.save()
    except Order.DoesNotExist:
        # Try updating Print Order
        try:
            print_order = PrintOrder.objects.get(id=order_id, distributor=distributor)
            print_order.payment_status = status
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

        # Get additional images and their colors
        additional_images = request.FILES.getlist('additional_images')
        image_colors = request.POST.getlist('image_colors')

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

        # ---------- SAVE ADDITIONAL IMAGES ----------
        if additional_images:
            for img_file, color_name in zip(additional_images, image_colors):
                if color_name.strip():
                    # Find the color variation
                    color_variation = Variation.objects.filter(
                        product=product,
                        variation_category='color',
                        variation_value=color_name.strip()
                    ).first()
                    if color_variation:
                        ProductImage.objects.create(
                            product=product,
                            variation=color_variation,
                            image=img_file
                        )

        return redirect('distributor_dashboard')


    return render(request, 'distributor/add_product.html', {
        'categories': categories
    })

@login_required
def edit_product(request, product_id):
    distributor = request.user.distributor_profile
    product = get_object_or_404(Product, id=product_id, distributor=distributor)
    categories = Category.objects.all()

    if request.method == "POST":
        product.product_name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = int(request.POST.get('stock'))
        
        selected_category_id = request.POST.get('category')
        new_category_name = request.POST.get('new_category')
        new_category_image = request.FILES.get('new_category_image')

        if new_category_name:
            category, created = Category.objects.get_or_create(
                category_name=new_category_name,
                defaults={
                    "slug": slugify(new_category_name),
                    "cat_image": new_category_image
                }
            )
            product.category = category
        elif selected_category_id:
            product.category = Category.objects.get(id=selected_category_id)

        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()
        return redirect('distributor_dashboard')

    return render(request, 'distributor/edit_product.html', {
        'product': product,
        'categories': categories,
    })

@login_required
def distributor_orders(request):

    distributor = request.user.distributor_profile
    
    # Fetch Standard Orders
    orders = Order.objects.filter(distributor=distributor).prefetch_related('returns').annotate(
        order_date=TruncDate('created_at')
    ).order_by('-created_at')
    
    # Fetch Print/Custom Orders
    print_orders = PrintOrder.objects.filter(distributor=distributor).select_related(
        'store_order_item__order'
    ).prefetch_related(
        'store_order_item__order__returns'
    ).annotate(
        order_date=TruncDate('created_at')
    ).order_by('-created_at')

    # Collect unique returns for modals using a dictionary to ensure uniqueness by ID
    unique_returns = {}
    
    # Collect from standard orders
    for o in orders:
        for r in o.returns.all():
            unique_returns[r.id] = r
            
    # Collect from print orders
    for po in print_orders:
        if po.store_order_item and po.store_order_item.order:
            for r in po.store_order_item.order.returns.all():
                unique_returns[r.id] = r

    return render(request, 'distributor/orders.html', {
        'orders': orders,
        'print_orders': print_orders,
        'returns_to_show': unique_returns.values()
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


# ================= RETURN VIEWS =================

@login_required
def create_return(request, order_id):
    """Create a return request for an order"""
    from datetime import timedelta
    from django.utils import timezone
    from .models import Return
    from store.models import Order, OrderItem
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if all items in order are delivered
    from .models import Order as DistributorOrder, PrintOrder as DistributorPrintOrder
    
    # Robust check: Check if distributor app says it's delivered
    distributor_delivered = False
    
    # Check if a linked PrintOrder is delivered
    print_orders = DistributorPrintOrder.objects.filter(user=request.user, store_order_item__order=order)
    if print_orders.exists():
        distributor_delivered = all(po.delivery_status == 'delivered' for po in print_orders)
    else:
        # Check if a standard Order matches
        standard_orders = DistributorOrder.objects.filter(user=request.user, total_price=order.total)
        if standard_orders.exists():
            distributor_delivered = all(so.delivery_status == 'delivered' for so in standard_orders)

    # Check the store items directly as well
    order_items = OrderItem.objects.filter(order=order)
    if not order_items.exists():
        messages.error(request, "Order has no items.")
        return redirect('order_history')
    
    # Allow return if EITHER the store status OR the distributor status is delivered
    store_delivered = all(item.status == 'Delivered' for item in order_items)
    
    if not (store_delivered or distributor_delivered):
        messages.error(request, "Order must be fully delivered to create a return request.")
        return redirect('order_history')
    
    # Check if return already exists for this order
    if order.returns.filter(return_status__in=['pending', 'approved']).exists():
        messages.warning(request, "A return request already exists for this order.")
        return redirect('order_history')
    
    # Check if within 7 days
    days_passed = (timezone.now() - order.created_at).days
    if days_passed > 7:
        messages.error(request, "Return window has expired. Returns are only available for 7 days after delivery.")
        return redirect('order_history')
    
    if request.method == "POST":
        issue_description = request.POST.get('issue_description')
        photo = request.FILES.get('photo')
        
        if not issue_description:
            messages.error(request, "Please describe the issue.")
            return redirect('create_return', order_id=order_id)
        
        if not photo:
            messages.error(request, "Please upload a photo of the issue.")
            return redirect('create_return', order_id=order_id)
        
        # Create return request
        return_obj = Return.objects.create(
            order=order,
            user=request.user,
            issue_description=issue_description,
            photo=photo,
            return_status='pending'
        )
        
        messages.success(request, "Return request created successfully. Our team will review it shortly.")
        return redirect('order_history')
    
    return render(request, 'shop/create_return.html', {
        'order': order,
        'days_remaining': 7 - days_passed
    })


@login_required
def view_returns(request):
    """View all returns for current user"""
    from .models import Return
    
    returns = Return.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'shop/returns.html', {
        'returns': returns
    })


@login_required
def distributor_returns(request):
    """View all returns for distributor's orders"""
    from .models import Return
    from store.models import OrderItem
    
    try:
        distributor = request.user.distributor_profile
    except:
        messages.error(request, "You are not a distributor.")
        return redirect('shop')
    
    # Get all orders that contain items from this distributor
    distributor_order_items = OrderItem.objects.filter(distributor=distributor)
    distributor_orders = set(item.order for item in distributor_order_items)
    
    returns = Return.objects.filter(
        order__in=list(distributor_orders)
    ).order_by('-created_at')
    
    # Calculate summary counts for the dashboard
    pending_count = returns.filter(return_status='pending').count()
    approved_count = returns.filter(return_status='approved').count()
    completed_count = returns.filter(return_status='completed').count()
    
    return render(request, 'distributor/returns.html', {
        'returns': returns,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count
    })


@login_required
def update_return_status(request, return_id):
    """Update return status (approve/reject)"""
    from .models import Return
    from store.models import OrderItem
    
    try:
        distributor = request.user.distributor_profile
    except:
        messages.error(request, "You are not a distributor.")
        return redirect('shop')
    
    return_obj = get_object_or_404(Return, id=return_id)
    
    # Check if distributor has items in this order
    distributor_items = OrderItem.objects.filter(
        order=return_obj.order,
        distributor=distributor
    )
    
    if not distributor_items.exists():
        messages.error(request, "You don't have permission to update this return.")
        return redirect('distributor_returns')
    
    if request.method == "POST":
        new_status = request.POST.get('status')
        
        if new_status in ['approved', 'rejected', 'completed']:
            return_obj.return_status = new_status
            return_obj.save()
            
            action_text = "approved" if new_status == 'approved' else "rejected" if new_status == 'rejected' else "completed"
            messages.success(request, f"Return request {action_text} successfully.")
        
    return redirect('distributor_returns')