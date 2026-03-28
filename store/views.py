from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from types import SimpleNamespace
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order, OrderItem, Variation, ReviewRating, ProductImage
from category.models import Category
from .forms import ReviewForm
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from orders.models import Address, PrintOrder, UploadedDesign
from orders.models import Product as DistributorProduct
from django.http import JsonResponse
# ================= STORE =================
def store(request, category_slug=None):
    category = None
    products = None
    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category, is_available=True)
    else:
        products = Product.objects.all().filter(is_available=True)

    distributor = None
    if request.user.is_authenticated:
        distributor = getattr(request.user, 'distributor_profile', None)

    return render(request, 'store/store.html', {
        'products': products,
        'distributor': distributor,
        'category': category
    })

# ================= PRODUCT DETAIL =================
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Fetch 6 related products from the same category, excluding the current one, ordered by newest
    related_products = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id).order_by('-created_date')[:6]
    
    orderproduct = False
    if request.user.is_authenticated:
        orderproduct = OrderItem.objects.filter(order__user=request.user, product_id=product.id).exists()
    
    reviews = ReviewRating.objects.filter(product_id=product.id, status=True).order_by('-updated_at')
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'orderproduct': orderproduct,
        'reviews': reviews,
    })


# ================= GET IMAGE FOR COLOR =================
def get_image_for_color(request, product_id, color):
    product = get_object_or_404(Product, id=product_id)
    image_url = product.get_image_for_color(color)
    return JsonResponse({'image_url': image_url})


# ================= ADD TO CART =================
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variation = []
    
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass
        
        # Check if color and size are required but not provided
        available_colors = product.variation_set.filter(variation_category='color', is_active=True).exists()
        available_sizes = product.variation_set.filter(variation_category='size', is_active=True).exists()
        
        selected_categories = [v.variation_category for v in product_variation]
        
        if request.POST.get('is_product_detail'):
            if available_colors and 'color' not in selected_categories:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': "Please select a color."})
                messages.error(request, "Please select a color.")
                return redirect(request.META.get('HTTP_REFERER', 'product_detail'))
                
            if available_sizes and 'size' not in selected_categories:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': "Please select a size."})
                messages.error(request, "Please select a size.")
                return redirect(request.META.get('HTTP_REFERER', 'product_detail'))

    if not product.is_available:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': "Product is not available for sale"})
        messages.error(request, "Product is not available for sale")
        return redirect('store')

    # If it's a Buy Now click
    if request.POST.get('buy_now'):
        request.session['buy_now_item'] = {
            'product_id': product_id,
            'variations': [v.id for v in product_variation],
            'quantity': 1
        }
        return redirect('checkout')
    
    # Normal Add to Cart (Clear any previous Buy Now session)
    if 'buy_now_item' in request.session:
        del request.session['buy_now_item']

    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Helper function to compare variation sets
    def variations_match(var_list1, var_list2):
        if len(var_list1) != len(var_list2):
            return False
        
        # Create sets of (category, value) tuples for comparison
        set1 = set((v.variation_category.lower(), v.variation_value.lower()) for v in var_list1)
        set2 = set((v.variation_category.lower(), v.variation_value.lower()) for v in var_list2)
        
        return set1 == set2

    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
    
    if is_cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        
        # Find matching cart item with same variations
        matching_item = None
        for cart_item in cart_items:
            existing_variations = list(cart_item.variations.all())
            if variations_match(product_variation, existing_variations):
                matching_item = cart_item
                break
        
        if matching_item:
            # Increase quantity for matching item
            if matching_item.quantity + 1 > product.stock:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'warning', 'message': f"Sorry, only {product.stock} units are available."})
                messages.warning(request, f"Sorry, only {product.stock} units of {product.product_name} are available.")
                return redirect(request.META.get('HTTP_REFERER', 'cart'))
            matching_item.quantity += 1
            matching_item.save()
        else:
            # Create new cart item with these variations
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variation) > 0:
                item.variations.add(*product_variation)
            item.save()
    else:
        # Product not in cart, create new cart item
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
        )
        if len(product_variation) > 0:
            cart_item.variations.add(*product_variation)
        cart_item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
        return JsonResponse({
            'status': 'success',
            'message': f"{product.product_name} added to cart!",
            'cart_count': cart_count
        })

    return redirect(request.META.get('HTTP_REFERER', 'cart'))


# ================= CART PAGE =================
@login_required
def cart(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)

    total = sum(item.sub_total() for item in cart_items)

    return render(request, "store/cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


@login_required
def increase_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if item.quantity + 1 > item.product.stock:
        messages.warning(request, f"Only {item.product.stock} left in stock. You can order maximum {item.product.stock} items.")
    else:
        item.quantity += 1
        item.save()
    return redirect('cart')


# ================= DECREASE =================
@login_required
def decrease_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect('cart')


# ================= REMOVE =================
@login_required
def remove_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart')


# ================= CONTACT =================
def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )

        messages.success(request, "Message sent successfully!")

    return render(request, "contact.html")


# ================= CHECKOUT (STEP 1) =================
@login_required
def checkout(request):
    buy_now_item_data = request.session.get('buy_now_item')
    
    if buy_now_item_data:
        product = get_object_or_404(Product, id=buy_now_item_data['product_id'])
        variations = Variation.objects.filter(id__in=buy_now_item_data['variations'])
        
        # Create a mock object that behaves like a CartItem
        item = SimpleNamespace(
            product=product,
            quantity=buy_now_item_data['quantity'],
            variations=SimpleNamespace(
                all=lambda: variations,
                exists=lambda: variations.exists()
            ),
            sub_total=lambda: product.price * buy_now_item_data['quantity']
        )
        cart_items = [item]
        total = item.sub_total()
    else:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty")
            return redirect('cart')
        total = sum(item.sub_total() for item in cart_items)

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        if not payment_method:
            messages.error(request, "Please select payment method")
            return redirect('checkout')

        # ---------- ADDRESS HANDLING ----------
        address_id = request.POST.get('address_id')
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
        else:
            address = Address.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                house=request.POST.get("house"),
                area=request.POST.get("area"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
                is_default=request.POST.get('set_as_default') == 'on'
            )
            if address.is_default:
                Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)

        # ---------- DESIGN UPLOAD (Optional) ----------
        design_file = request.FILES.get('design')
        uploaded_design = None
        if design_file:
            uploaded_design = UploadedDesign.objects.create(user=request.user, image=design_file)

        # ---------- PAYMENT PROOF (Optional) ----------
        payment_proof = request.FILES.get('payment_proof')

        # ---------- CREATE STORE ORDER ----------
        store_order = Order.objects.create(
            user=request.user,
            total=total
        )

        # ---------- CREATE ITEMS ----------
        for item in cart_items:
            product = item.product
            # Create OrderItem (Store Model)
            order_item = OrderItem.objects.create(
                order=store_order,
                product=product,
                distributor=product.distributor, # ADDED
                quantity=item.quantity,
                price=product.price if product.stock > 0 else 0
            )
            if item.variations.exists():
                order_item.variations.set(item.variations.all())

            # Create PrintOrder (Orders Model)
            print_order = PrintOrder.objects.create(
                user=request.user,
                product=product,
                design=uploaded_design,
                address=address,
                distributor=product.distributor,
                payment_method=payment_method,
                quantity=item.quantity,
                total_price=item.sub_total(),
                payment_proof=payment_proof,
                store_order_item=order_item # LINK HERE
            )
            # Set Payment Status
            if payment_method == "cod":
                print_order.payment_status = "cod_confirmed"
            elif payment_method == "qr":
                print_order.payment_status = "verification_pending"
            elif payment_method == "card":
                print_order.payment_status = "paid"
                print_order.card_number = request.POST.get("card_number")
                print_order.expiry_date = request.POST.get("expiry_date")
                print_order.cvv = request.POST.get("cvv")

            if item.variations.exists():
                print_order.variations.set(item.variations.all())
            print_order.save()

            # Update Stock
            if product.stock > 0:
                product.stock = max(0, product.stock - item.quantity)
                product.save()

        # ---------- SEND EMAIL ----------
        try:
            subject = f"Order Placed Successfully - Order #{store_order.id}"
            body = f"Hi {request.user.username},\n\nYour order has been placed successfully!\nOrder ID: #{store_order.id}\nTotal Amount: ₹{total}\n\nThank you for shopping with us!"
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True
            )
        except:
            pass

        # ---------- CLEAR CART / SESSION ----------
        if request.session.get('buy_now_item'):
            del request.session['buy_now_item']
        else:
            cart_items.delete()

        messages.success(request, "🎉 Order placed successfully!")
        return redirect('store')

    return render(request, "store/checkout.html", {
        "cart_items": cart_items,
        "total": total,
        "addresses": addresses
    })


# ================= PAYMENT (STEP 2) =================
@login_required
def payment(request):

    cart_items = CartItem.objects.filter(cart__user=request.user)

    if not cart_items.exists():
        return redirect('cart')

    address_data = request.session.get("address")

    if not address_data:
        messages.error(request, "Please enter address first")
        return redirect('checkout')

    if request.method == "POST":

        payment_method = request.POST.get("payment_method")

        if not payment_method:
            messages.error(request, "Please select payment method")
            return redirect('payment')

        # SAVE ADDRESS TO DB
        address = Address.objects.create(
            user=request.user,
            **address_data
        )

        # CALCULATE TOTAL
        order_total = sum(item.sub_total() for item in cart_items)

        # CREATE STORE ORDER
        store_order = Order.objects.create(
            user=request.user,
            total=order_total
        )

        # CREATE ORDER FOR EACH CART ITEM
        for item in cart_items:

            product = item.product

            # Create OrderItem (Store Model)
            order_item = OrderItem.objects.create(
                order=store_order,
                product=product,
                distributor=product.distributor, # ADDED
                quantity=item.quantity,
                price=product.price if product.stock > 0 else 0
            )
            # Transfer variations
            if item.variations.exists():
                order_item.variations.set(item.variations.all())
                order_item.save()

            # Create PrintOrder (Orders Model) - specifically for distributor visibility
            print_order = PrintOrder.objects.create(
                user=request.user,
                product=product,
                design=None,
                address=address,
                distributor=product.distributor,
                payment_method=payment_method,
                quantity=item.quantity,
                total_price=item.sub_total(),
                store_order_item=order_item # LINK HERE
            )
            # Transfer variations to PrintOrder
            if item.variations.exists():
                print_order.variations.set(item.variations.all())
                print_order.save()

            
            # Update Stock
            if product.stock > 0:
                product.stock = max(0, product.stock - item.quantity)
                product.save()

        # CLEAR CART
        cart_items.delete()

        # CLEAR SESSION ADDRESS
        if "address" in request.session:
            del request.session["address"]

        messages.success(request, "🎉 Order placed successfully!")
        return redirect('store')

    # Pass total to template
    total = sum(item.sub_total() for item in cart_items)

    return render(request, "store/payment.html", {"total": total})


# ================= ORDER HISTORY =================
@login_required
def order_history(request):
    # Fetch all order items for the user, sorted by the order date
    order_items = OrderItem.objects.filter(order__user=request.user).order_by('-order__created_at', '-id')

    return render(request, "store/order_history.html", {
        "order_items": order_items
    })

@login_required
def delete_product(request, product_id):

    distributor = request.user.distributor_profile

    product = get_object_or_404(
        Product,
        id=product_id,
        distributor=distributor   # 🔐 ensures ownership
    )

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully")

    return redirect('distributor_dashboard')
@login_required
def distributor_dashboard(request):

    distributor = request.user.distributor_profile

    products = Product.objects.filter(distributor=distributor)

    return render(request, 'distributor/dashboard.html', {
        'products': products
    })

def search(request):
    import difflib
    keyword = request.GET.get('keyword', '')
    products = Product.objects.none()
    product_count = 0

    if keyword:
        # First attempt: Simple case-insensitive search
        products = Product.objects.order_by('-created_date').filter(
            Q(description__icontains=keyword) | 
            Q(product_name__icontains=keyword)
        )
        product_count = products.count()

        # Fuzzy search if no results found
        if product_count == 0:
            all_names = list(Product.objects.filter(is_available=True).values_list('product_name', flat=True))
            matches = difflib.get_close_matches(keyword.lower(), [name.lower() for name in all_names], n=3, cutoff=0.5)
            
            if matches:
                query = Q()
                for match in matches:
                    query |= Q(product_name__icontains=match)
                products = Product.objects.order_by('-created_date').filter(query)
                product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
        'keyword': keyword,
    }
    return render(request, 'store/store.html', context)

@login_required
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER') or 'store'
    if request.method == 'POST':
        # Ensure user purchased
        has_purchased = OrderItem.objects.filter(order__user=request.user, product_id=product_id).exists()
        if not has_purchased:
            messages.error(request, "You must purchase this product to post a review.")
            return redirect(url)

        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, request.FILES, instance=reviews)
            if form.is_valid():
                form.save()
                messages.success(request, 'Thank you! Your review has been updated.')
            else:
                messages.error(request, "Invalid form data.")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST, request.FILES)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.image = form.cleaned_data['image']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
            else:
                messages.error(request, "Invalid form data.")
                return redirect(url)
    return redirect(url)

@login_required
def write_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Check if user purchased the product and it was delivered
    has_purchased = OrderItem.objects.filter(order__user=request.user, product_id=product_id, status='Delivered').exists()
    
    if not has_purchased:
        messages.error(request, "You can only review products that have been delivered to you.")
        return redirect('order_history')

    review = ReviewRating.objects.filter(user=request.user, product=product).first()
    
    if request.method == 'POST':
        if review:
            form = ReviewForm(request.POST, request.FILES, instance=review)
        else:
            form = ReviewForm(request.POST, request.FILES)
            
        if form.is_valid():
            data = form.save(commit=False)
            data.user = request.user
            data.product = product
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect('order_history')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'store/write_review.html', {
        'product': product,
        'form': form,
        'review': review
    })

def support(request):
    return render(request, 'store/support.html')