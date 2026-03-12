from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class MyAccountManager(BaseUserManager):

    def create_user(self, email, username, first_name, last_name, password=None, role='customer'):

        if not email:
            raise ValueError("User must have email")

        email = self.normalize_email(email)

        user = self.model(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=role,   # ✅ THIS LINE FIXES EVERYTHING
    )

        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password):

        user = self.create_user(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password,
        role='customer'   # keep safe
    )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)

        return user



class Account(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('distributor', 'Distributor'),
    )

    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)
    username   = models.CharField(max_length=50, unique=True)
    email      = models.EmailField(max_length=50, unique=True)

    phone_num  = models.CharField(max_length=20, blank=True, null=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login  = models.DateTimeField(auto_now=True)

    is_admin  = models.BooleanField(default=False)
    is_staff  = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True