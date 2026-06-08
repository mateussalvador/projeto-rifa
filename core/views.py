from django.http import HttpResponse
from django.shortcuts import render
from .models import Rifa

def home(request):
    return render(request, 'core/pages/home.html', context={
        'rifas': Rifa.objects.all().order_by('-id'),
    })

def sobre(request):
    html = '''
    <h1 align="center">Sobre</h1>
    <p align="center">Este será um sistema de rifas.</p>
    '''
    return HttpResponse(html)