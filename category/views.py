from django.shortcuts import render
from .models import Category

def all_categories(request):
    categories = Category.objects.all()
    return render(request, "category/all_categories.html", {
        "categories": categories
    })