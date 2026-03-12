from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_categories, name='all_categories'),
]