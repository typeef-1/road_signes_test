from django.shortcuts import render, redirect

# Create your views here.

from django.core.handlers.wsgi import WSGIRequest

from django.views.generic import TemplateView

def landingPage(request: WSGIRequest):
    context={}
    return render(request, 'landing_page.html', context)