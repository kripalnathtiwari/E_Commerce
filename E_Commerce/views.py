from django.http import HttpResponse
from django.shortcuts import render, redirect
from store.models import Product
from category.models import Category

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('-created_date')
    slider_products = products[:6]
    categories = Category.objects.all()

    context={
        'products': products,
        'slider_products': slider_products,
        'categories': categories,
    }
    return render(request, 'E_Commerce/home.html', context)

