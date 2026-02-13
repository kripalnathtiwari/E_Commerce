from django.http import HttpResponse
from django.contrib import redirects
from django.shortcuts import render
def home(request):
    return render(request, 'E_commerce/home.html')

