import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CheckoutForm, RegistroForm, RifaForm
from .models import Compra, NumerosRifa, Rifa


def home(request):
    return render(request, 'core/pages/home.html', context={
        'rifas': Rifa.objects.all().order_by('-id'),
    })


def rifas(request, id):
    rifa = get_object_or_404(Rifa, id=id)
    numeros = rifa.grade_numeros.all()

    total = rifa.qtd_numeros
    pagos = numeros.filter(status='PAGO').count()
    reservados = numeros.filter(status='RESERVADO').count()
    porcentagem_progresso = int((pagos / total) * 100) if total > 0 else 0

    # Carrega todos os usuários para o dropdown de escolha de vendedor parceiro
    vendedores = User.objects.all()

    # Mapeia a grade para identificar quais números foram 
    # reservados pelo usuário logado
    for n in numeros:
        if n.status == 'RESERVADO' and n.compra and request.user.is_authenticated:  # noqa: E501
            n.pessoal = (n.compra.comprador == request.user)
        else:
            n.pessoal = False

    return render(request, 'core/pages/rifa.html', context={
        'rifa': rifa,
        'numeros': numeros,
        'pagos': pagos,
        'reservados': reservados,
        'porcentagem': porcentagem_progresso,
        'vendedores': vendedores,
    })


def cadastrar_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect('home')
    else:
        form = RegistroForm()
    return render(request, 'core/pages/cadastro.html', {'form': form})


def login_usuario(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # O next garante que se ele veio barrado de uma compra, 
                # ele volte para concluir a ação
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/pages/login.html', {'form': form})


def logout_usuario(request):
    logout(request)
    return redirect('home')


@login_required
def criar_rifa(request):
    if request.method == 'POST':
        form = RifaForm(request.POST, request.FILES)
        if form.is_valid():
            rifa = form.save(commit=False)
            rifa.autor = request.user
            rifa.save()
            messages.success(request, "Rifa criada com sucesso!")
            return redirect('home')
    else:
        form = RifaForm()
    return render(request, 'core/pages/criar_rifa.html', {'form': form})


@login_required
def reservar_numero(request, rifa_id, numero):
    if request.method != 'POST':
        return redirect('rifas', id=rifa_id)

    rifa = get_object_or_404(Rifa, id=rifa_id)
    numero_rifa = get_object_or_404(NumerosRifa, rifa=rifa, numero=numero)
    
    if numero_rifa.status != 'DISPONIVEL':
        messages.error(request, "Este número já foi reservado ou pago.")
        return redirect('rifas', id=rifa.id)
        
    vendedor_id = request.POST.get('vendedor')
    vendedor_selecionado = None
    
    # Se um vendedor foi de fato escolhido, busca o objeto correspondente
    if vendedor_id:
        vendedor_selecionado = User.objects.filter(id=vendedor_id).first()

    compra = Compra.objects.create(
        comprador=request.user,
        rifa=rifa,
        vendedor_associado=vendedor_selecionado,
        status='PENDENTE'
    )

    numero_rifa.status = 'RESERVADO'
    numero_rifa.compra = compra
    numero_rifa.save()

    return redirect('detalhe_compra', compra_id=compra.id)


@login_required
def detalhe_compra(request, compra_id):
    # Restringe o acesso apenas ao comprador dono da reserva
    compra = get_object_or_404(Compra, id=compra_id, comprador=request.user)
    if request.method == 'POST':
        form = CheckoutForm(request.POST, request.FILES, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, "Comprovante enviado! Aguarde a validação do organizador.")  # noqa: E501
            return redirect('home')
    else:
        form = CheckoutForm(instance=compra)
    return render(request, 'core/pages/detalhe_compra.html', {'compra': compra, 'form': form})  # noqa: E501


@login_required
def cancelar_reserva(request, compra_id):
    # Garante segurança para que ninguém cancele a reserva alheia
    compra = get_object_or_404(Compra, id=compra_id, comprador=request.user)

    if compra.status == 'PENDENTE':
        numero_rifa = NumerosRifa.objects.filter(compra=compra).first()
        if numero_rifa:
            numero_rifa.status = 'DISPONIVEL'
            numero_rifa.compra = None
            numero_rifa.save()

        rifa_id = compra.rifa.id
        compra.delete()
        messages.success(request, "Sua reserva foi cancelada com sucesso e o número está livre para novos compradores.")  # noqa: E501
        return redirect('rifas', id=rifa_id)
    else:
        messages.error(request, "Não é possível cancelar uma reserva que já foi paga ou expirada.")  # noqa: E501
        return redirect('home')


@login_required
def meu_painel(request):
    # Filtra apenas as rifas que o usuário logado criou
    minhas_rifas = Rifa.objects.filter(autor=request.user).order_by('-id')
    return render(request, 'core/pages/meu_painel.html', {'minhas_rifas': minhas_rifas})  # noqa: E501


@login_required
def realizar_sorteio(request, rifa_id):
    # Busca a rifa garantindo que quem está 
    # tentando sortear é o próprio dono/criador dela
    rifa = get_object_or_404(Rifa, id=rifa_id, autor=request.user)

    if rifa.finalizada:
        return JsonResponse({'success': False, 'message': 'Este sorteio já foi realizado!'}, status=400)  # noqa: E501

    # Filtra apenas os números que foram pagos[cite: 1]
    numeros_pagos = rifa.grade_numeros.filter(status='PAGO')

    if not numeros_pagos.exists():
        return JsonResponse({'success': False, 'message': 'Não é possível realizar o sorteio. Nenhum número foi pago ainda!'}, status=400)  # noqa: E501

    # Seleciona aleatoriamente um dos números pagos de forma justa[cite: 1]
    numero_sorteado = random.choice(numeros_pagos)

    # Vincula o resultado oficial[cite: 1]
    rifa.numero_ganhador = numero_sorteado.numero
    rifa.ganhador = numero_sorteado.compra.comprador
    rifa.finalizada = True
    rifa.data_sorteio = timezone.now()
    rifa.save()

    # Retorna o número e o nome do ganhador para o JavaScript[cite: 1]
    return JsonResponse({
        'success': True,
        'numero_ganhador': rifa.numero_ganhador,
        'ganhador_username': rifa.ganhador.username
    })


def verificar_expiracoes_reservas():
    """
    Sprint 9-10: Rotina que varre o banco liberando números de reservas
    que foram criadas há mais de 24 horas (1 dia) e continuam PENDENTES.
    """
    tempo_limite = timezone.now() - timedelta(days=1)

    # CORRIGIDO: Removidas as chaves de {tempo_limite}
    compras_expiradas = Compra.objects.filter(status='PENDENTE', data_compra__lt=tempo_limite)  # noqa: E501

    for compra in compras_expiradas:
        # Libera os números associados na grade
        numero_rifa = NumerosRifa.objects.filter(compra=compra).first()
        if numero_rifa:
            numero_rifa.status = 'DISPONIVEL'
            numero_rifa.compra = None
            numero_rifa.save()
 
        # Marca a compra como expirada
        compra.status = 'EXPIRADO'
        compra.save()


@login_required
def gerenciar_comprovantes(request):
    # Executa a limpeza automática de pendências com mais de 1 dia
    verificar_expiracoes_reservas()

    # Busca as compras pendentes das rifas criadas pelo organizador logado
    compras_pendentes = Compra.objects.filter(
        rifa__autor=request.user,
        status='PENDENTE'
    ).exclude(comprovante='').order_by('data_compra')

    return render(request, 'core/pages/gerenciar_comprovantes.html', {'compras': compras_pendentes})  # noqa: E501


@login_required
def aprovar_comprovante(request, compra_id):
    # Garante que apenas o dono da rifa possa aprovar o pagamento
    compra = get_object_or_404(Compra, id=compra_id, rifa__autor=request.user)

    compra.status = 'PAGO'
    compra.save()

    # Atualiza o status do número na grade para PAGO definitivamente
    numero_rifa = NumerosRifa.objects.filter(compra=compra).first()
    if numero_rifa:
        numero_rifa.status = 'PAGO'
        numero_rifa.save()

    messages.success(request, f"Pagamento do pedido #{compra.id} aprovado com sucesso! O número agora está marcado como Pago.")  # noqa: E501
    return redirect('gerenciar_comprovantes')


@login_required
def recusar_comprovante(request, compra_id):
    # Garante que apenas o dono da rifa possa recusar o pagamento
    compra = get_object_or_404(Compra, id=compra_id, rifa__autor=request.user)

    # Libera o número de volta para a grade
    numero_rifa = NumerosRifa.objects.filter(compra=compra).first()
    if numero_rifa:
        numero_rifa.status = 'DISPONIVEL'
        numero_rifa.compra = None
        numero_rifa.save()

    compra.delete()  # Remove a intenção de compra inválida
    messages.warning(request, f"Comprovante do pedido #{compra_id} recusado. O número voltou a ficar livre na grade.")  # noqa: E501
    return redirect('gerenciar_comprovantes')
