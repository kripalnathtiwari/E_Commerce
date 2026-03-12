from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from orders.models import Distributor
User = get_user_model()

# -------- SIGNUP --------
from orders.models import Distributor

def signup(request):

    if request.method == "POST":

        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name') 
        username   = request.POST.get('username')
        email      = request.POST.get('email')
        password   = request.POST.get('password')
        confirm    = request.POST.get('confirm')
        role       = request.POST.get('role', 'customer').lower()

        phone      = request.POST.get('phone')
        city       = request.POST.get('city')

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect('signup')

        # ✅ CHECK IF USERNAME OR EMAIL ALREADY EXISTS
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return redirect('signup')

        try:
            # ✅ CREATE USER
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=role
            )
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('signup')

        # ✅ CREATE DISTRIBUTOR ONLY IF ROLE MATCHES
        if role == 'distributor':

            if not phone or not city:
                messages.error(request, "Phone & City required for distributor")
                user.delete()
                return redirect('signup')

            Distributor.objects.create(
                user=user,
                phone=phone,
                city=city
            )

        messages.success(request, "Account created. Please login.")
        return redirect('login')

    # ✅ GET request comes here safely
    return render(request, "accounts/signup.html")
# -------- LOGIN --------
def login_view(request):
    if request.method == "POST":

        email    = request.POST.get('username')
        password = request.POST.get('password')
        role     = request.POST.get('role', 'customer').lower()

        user = authenticate(request, username=email, password=password)

        if user is not None:

            if user.role.lower() != role:
                messages.error(request, "Wrong login type selected")
                return redirect('login')

            login(request, user)

            if user.role == 'distributor':
                return redirect('distributor_dashboard')
            else:
                return redirect('home')

        else:
            messages.error(request, "Invalid email or password")

    return render(request, "accounts/login.html")
# -------- LOGOUT --------
def logout_view(request):
    logout(request)
    return redirect('home')