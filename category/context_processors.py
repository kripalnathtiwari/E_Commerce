from .models import Category

def menu_categories(request):
    return {
        'menu_categories': Category.objects.all()
    }