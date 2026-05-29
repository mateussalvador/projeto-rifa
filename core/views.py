from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    dados = {'nome': 'Mateus Salvador', 'profissao': 'Desenvolvedor Python e Analista de Dados'}
    return render(request, 'core/pages/home.html', dados)

def sobre(request):
    html = '''
    <h1 align="center">Sobre</h1>
    <p align="center">Este será um sistema de rifas.</p>
    '''
    return HttpResponse(html)