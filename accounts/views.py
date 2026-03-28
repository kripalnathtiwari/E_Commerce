from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from django.utils import timezone
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
        login_method = request.POST.get('login_method', 'password')
        role     = request.POST.get('role', 'customer').lower()

        user = None
        if login_method == 'password':
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)
            if user is None:
                messages.error(request, "Invalid email or password")
                return redirect('login')
        else:
            # Login via OTP (Passwordless)
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No account found with this email.")
                return redirect('login')

        if user is not None:
            if user.role.lower() != role:
                messages.error(request, "Wrong login type selected")
                return redirect('login')

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['otp_user_id'] = user.id
            request.session['otp_role'] = role
            request.session['otp_expiry'] = (timezone.now() + timezone.timedelta(minutes=5)).isoformat()

            # Send Email
            try:
                subject = "Your Login OTP"
                message = f"Hello {user.first_name},\n\nYour One-Time Password (OTP) for login is: {otp}\n\nThis OTP will expire in 5 minutes.\n\nThank you!"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, f"An OTP has been sent to {user.email}")
                return redirect('verify_otp')
            except Exception as e:
                messages.error(request, f"Error sending email: {str(e)}")
                return redirect('login')

    return render(request, "accounts/login.html")

# -------- VERIFY OTP --------
def verify_otp(request):
    if 'otp_user_id' not in request.session:
        return redirect('login')

    if request.method == "POST":
        user_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        expiry_str = request.session.get('otp_expiry')
        user_id = request.session.get('otp_user_id')

        if not session_otp or not expiry_str:
            messages.error(request, "OTP expired or invalid. Please try login again.")
            return redirect('login')

        expiry_time = timezone.datetime.fromisoformat(expiry_str)
        if timezone.now() > expiry_time:
            messages.error(request, "OTP expired. Please try login again.")
            del request.session['otp']
            return redirect('login')

        if user_otp == session_otp:
            user = User.objects.get(id=user_id)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            # Clear session
            del request.session['otp']
            del request.session['otp_user_id']
            del request.session['otp_role']
            del request.session['otp_expiry']

            if user.role == 'distributor':
                return redirect('distributor_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "accounts/verify_otp.html")
# -------- LOGOUT --------
def logout_view(request):
    logout(request)
    return redirect('home')