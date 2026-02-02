from django.shortcuts import render, redirect

# Create your views here.

from django.core.handlers.wsgi import WSGIRequest

def index_page(req: WSGIRequest):
    context = {}
    return render(req, 'index.html', context)
