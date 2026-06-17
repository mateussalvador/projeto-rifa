from django.shortcuts import render

from .models import Rifa


def home(request):
    return render(request, 'core/pages/home.html', context={
        'rifas': Rifa.objects.all().order_by('-id'),
        'id': Rifa.objects.all().order_by('-id'),
    })


def rifas(request, id):
    return render(request, 'core/pages/rifa.html', context={
        'id': id,
        'titulo': Rifa.objects.filter(id=id),
    })
