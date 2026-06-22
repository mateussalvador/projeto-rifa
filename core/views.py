import csv
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout  # noqa
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import (  # noqa: E501
    CheckoutForm,
    ComentarioForm,
    RegistroForm,
    RifaForm,
    VendedorForm,
)
from .models import (  # noqa
    Comentario,
    Compra,
    NumerosRifa,
    PerfilUsuario,
    Rifa,
    VendedorRifa,
)


# =====================================================================
# ROTINAS AUTOMATIZADAS (BACKGROUND)
# =====================================================================
def verificar_expiracoes_reservas():
    tempo_limite = timezone.now() - timedelta(days=1)
    compras_expiradas = Compra.objects.filter(status='PENDENTE', data_compra__lt=tempo_limite)  # noqa: E501

    for compra in compras_expiradas:
        numero_rifa = NumerosRifa.objects.filter(compra=compra).first()
        if numero_rifa:
            numero_rifa.status = 'DISPONIVEL'
            numero_rifa.compra = None
            numero_rifa.save()
        compra.status = 'EXPIRADO'
        compra.save()

# =====================================================================
# VISUALIZAÇÃO PÚBLICA E NAVEGAÇÃO
# =====================================================================


def home(request):
    verificar_expiracoes_reservas()
    rifas_lista = Rifa.objects.all().order_by('-data_criacao')
    return render(request, 'core/pages/home.html', {'rifas': rifas_lista})


def rifas(request, id):
    rifa = get_object_or_404(Rifa, id=id)
    numeros = rifa.grade_numeros.all()
    vendedores = User.objects.filter(perfil__papel='VENDEDOR', rifas_permitidas__rifa=rifa, rifas_permitidas__ativo=True)  # noqa: E501
    
    porcentagem = 0
    if rifa.qtd_numeros > 0:
        numeros_pagos = numeros.filter(status='PAGO').count()
        porcentagem = int((numeros_pagos / rifa.qtd_numeros) * 100)

    for n in numeros:
        n.pessoal = False
        if request.user.is_authenticated and n.compra and n.compra.comprador == request.user:  # noqa: E501
            n.pessoal = True

    # --- LÓGICA DE COMENTÁRIOS (COM TRAVA DE AUTENTICAÇÃO) ---
    comentarios_aprovados = rifa.comentarios.filter(status='APROVADO').order_by('-data_criacao')  # noqa: E501

    if request.method == 'POST' and 'form_comentario' in request.POST:
        # Trava de segurança no backend
        if not request.user.is_authenticated:
            messages.error(request, "Você precisa estar logado para comentar.")
            return redirect('login')

        form_comentario = ComentarioForm(request.POST)
        if form_comentario.is_valid():
            novo_comentario = form_comentario.save(commit=False)
            novo_comentario.rifa = rifa
            novo_comentario.save()

            # E-mail automático para o organizador avisando da interação
            if rifa.autor.email:
                assunto = f"Novo comentário aguardando moderação: {rifa.titulo}"  # noqa: E501
                mensagem = (
                    f"Olá, o usuário {novo_comentario.nome} acabou de deixar um comentário na sua rifa.\n\n"  # noqa: E501
                    f"Mensagem: {novo_comentario.texto}\n\n"
                    f"Acesse seu painel para aprovar ou rejeitar."
                )
                send_mail(assunto, mensagem, None, [rifa.autor.email])

            messages.success(request, "Seu comentário foi enviado e está aguardando aprovação do organizador!")  # noqa: E501
            return redirect('rifas', id=rifa.id)
    else:
        # Preenche automaticamente o nome e o 
        # e-mail se o usuário estiver logado
        if request.user.is_authenticated:
            form_comentario = ComentarioForm(initial={
                'nome': request.user.username,
                'email': request.user.email
            })
        else:
            form_comentario = ComentarioForm()

    return render(request, 'core/pages/rifa.html', {
        'rifa': rifa,
        'numeros': numeros,
        'vendedores': vendedores,
        'porcentagem': porcentagem,
        'comentarios': comentarios_aprovados,
        'form_comentario': form_comentario
    })

# =====================================================================
# AUTENTICAÇÃO E USUÁRIOS
# =====================================================================


def cadastrar_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bem-vindo, {user.username}! Conta criada com sucesso.")  # noqa: E501
            return redirect('home')
    else:
        form = RegistroForm()
    return render(request, 'core/pages/cadastro.html', {'form': form})


def login_usuario(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bem-vindo de volta, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Usuário ou senha incorretos.")
    else:
        form = AuthenticationForm()
    return render(request, 'core/pages/login.html', {'form': form})


def logout_usuario(request):
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect('home')

# =====================================================================
# CRIAÇÃO E GESTÃO DE RIFAS (ORGANIZADOR)
# =====================================================================


@login_required
def criar_rifa(request):
    if request.user.perfil.papel != 'ORGANIZADOR' and not request.user.is_superuser:  # noqa: E501
        messages.error(request, "Apenas organizadores podem criar rifas.")
        return redirect('home')

    if request.method == 'POST':
        form = RifaForm(request.POST, request.FILES)
        if form.is_valid():
            nova_rifa = form.save(commit=False)
            nova_rifa.autor = request.user
            nova_rifa.save()
            messages.success(request, "Rifa criada com sucesso! A grade de números foi gerada.")  # noqa: E501
            return redirect('meu_painel')
    else:
        form = RifaForm()
    return render(request, 'core/pages/criar_rifa.html', {'form': form})


@login_required
def meu_painel(request):
    minhas_rifas = Rifa.objects.filter(autor=request.user).order_by('-id')
    return render(request, 'core/pages/meu_painel.html', {'minhas_rifas': minhas_rifas})  # noqa: E501


@login_required
def gerenciar_comprovantes(request):
    verificar_expiracoes_reservas()
    compras_pendentes = Compra.objects.filter(
        rifa__autor=request.user,
        status='PENDENTE'
    ).exclude(comprovante='').order_by('data_compra')
    return render(request, 'core/pages/gerenciar_comprovantes.html', {'compras': compras_pendentes})  # noqa: E501


@login_required
def aprovar_comprovante(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id, rifa__autor=request.user)
    compra.status = 'PAGO'
    compra.save()

    numeros_vinculados = compra.numeros_alocados.all()  # noqa: E501 # Usa o related_name correto do seu model 
    for numero_rifa in numeros_vinculados:
        numero_rifa.status = 'PAGO'
        numero_rifa.save()

        # 📨 E-mail de confirmação de pagamento
        if compra.comprador.email:
            assunto = f"Pagamento Aprovado! Seu número da cota é {numero_rifa.numero}"  # noqa: E501
            mensagem = (
                f"Olá, {compra.comprador.username}!\n\n"
                f"Boa notícia! O organizador aprovou o seu pagamento para a rifa: '{compra.rifa.titulo}'.\n\n"  # noqa: E501
                f"Sua cota garantida é o número: {numero_rifa.numero}\n\n"
                f"Boa sorte no sorteio!"
            )
            send_mail(assunto, message=mensagem, from_email=None, recipient_list=[compra.comprador.email])  # noqa: E501

    messages.success(request, "Pagamento aprovado e cotas atualizadas para VERDE com sucesso!")  # noqa: E501
    return redirect('gerenciar_comprovantes')


@login_required
def recusar_comprovante(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id, rifa__autor=request.user)
    numero_rifa = NumerosRifa.objects.filter(compra=compra).first()

    # 📨 E-MAIL DE NOTIFICAÇÃO DE RECUSA (Enviado antes de deletar a compra)
    if compra.comprador.email:
        assunto = f"Problema com o seu comprovante - Rifa: {compra.rifa.titulo}"  # noqa: E501
        mensagem = (
            f"Olá, {compra.comprador.username}.\n\n"
            f"O seu comprovante enviado para a cota da rifa '{compra.rifa.titulo}' foi recusado pelo organizador.\n\n"  # noqa: E501
            f"Motivo: Os dados do PIX não coincidem ou a imagem estava ilegível.\n"  # noqa: E501
            f"Por conta disso, o número voltou a ficar disponível na grade para novos compradores.\n\n"  # noqa: E501
            f"Caso queira tentar novamente, acesse a plataforma e refaça a sua reserva."  # noqa: E501
        )
        send_mail(assunto, message=mensagem, from_email=None, recipient_list=[compra.comprador.email])  # noqa: E501

    if numero_rifa:
        numero_rifa.status = 'DISPONIVEL'
        numero_rifa.compra = None
        numero_rifa.save()

    compra.delete()
    messages.warning(request, "Comprovante recusado. A cota voltou a ficar disponível.")  # noqa: E501
    return redirect('gerenciar_comprovantes')


@login_required
def realizar_sorteio(request, rifa_id):
    rifa = get_object_or_404(Rifa, id=rifa_id, autor=request.user)

    if rifa.finalizada:
        return JsonResponse({'success': False, 'message': 'Este sorteio já foi realizado!'}, status=400)  # noqa: E501
    numeros_pagos = rifa.grade_numeros.filter(status='PAGO')

    if not numeros_pagos.exists():
        return JsonResponse({'success': False, 'message': 'Nenhum número pago para realizar o sorteio!'}, status=400)  # noqa: E501

    numero_sorteado = random.choice(numeros_pagos)
    rifa.numero_ganhador = numero_sorteado.numero
    rifa.ganhador = numero_sorteado.compra.comprador
    rifa.finalizada = True
    rifa.data_sorteio = timezone.now()
    rifa.save()

    # 📨 E-MAIL EXCLUSIVO PARA O GANHADOR DO PRÊMIO
    if rifa.ganhador.email:
        assunto = f"🎉 PARABÉNS! Você ganhou o sorteio da rifa: {rifa.titulo}"
        mensagem = (
            f"Olá, {rifa.ganhador.username}!!!\n\n"
            f"Você é o grande vencedor do sorteio da campanha '{rifa.titulo}'!\n\n"  # noqa: E501
            f"O seu número sorteado foi o: {rifa.numero_ganhador}\n\n"
            f"Entre em contato com o organizador ({rifa.autor.username}) para combinar a entrega do seu prêmio.\n\n"  # noqa: E501
            f"Parabéns novamente!"
        )
        send_mail(assunto, message=mensagem, from_email=None, recipient_list=[rifa.ganhador.email])  # noqa: E501

    return JsonResponse({
        'success': True,
        'numero_ganhador': rifa.numero_ganhador,
        'ganhador_username': rifa.ganhador.username
    })

# =====================================================================
# GESTÃO DE VENDEDORES (ORGANIZADOR)
# =====================================================================


@login_required
def gerenciar_vendedores(request):
    vendedores = User.objects.filter(perfil__papel='VENDEDOR', perfil__organizador_vinculado=request.user)  # noqa: E501
    rifas = Rifa.objects.filter(autor=request.user, finalizada=False)

    if request.method == 'POST':
        if 'form_vendedor' in request.POST:
            form = VendedorForm(request.POST)
            if form.is_valid():
                vendedor = form.save(commit=False)
                senha_gerada = get_random_string(length=8)
                vendedor.set_password(senha_gerada)
                vendedor.save()

                perfil = vendedor.perfil
                perfil.papel = 'VENDEDOR'
                perfil.organizador_vinculado = request.user
                perfil.telefone = form.cleaned_data.get('telefone')
                perfil.save()

                assunto = "Sua conta de Vendedor Parceiro foi criada!"
                mensagem = (
                    f"Olá {vendedor.username},\n\n"
                    f"O organizador {request.user.username} criou uma conta para você no Rifando.\n\n"  # noqa: E501
                    f"Suas credenciais:\n"
                    f"Usuário: {vendedor.username}\n"
                    f"Senha provisória: {senha_gerada}\n\n"
                    f"Acesse o sistema e acompanhe suas vendas!"
                )
                send_mail(assunto, mensagem, None, [vendedor.email])

                messages.success(request, f"Vendedor {vendedor.username} cadastrado com sucesso! Credenciais enviadas por e-mail.")  # noqa: E501
                return redirect('gerenciar_vendedores')

        elif 'form_associar' in request.POST:
            vendedor_id = request.POST.get('vendedor_id')
            rifa_id = request.POST.get('rifa_id')
            comissao = request.POST.get('comissao')

            vendedor_selecionado = get_object_or_404(User, id=vendedor_id)
            rifa_selecionada = get_object_or_404(Rifa, id=rifa_id)

            VendedorRifa.objects.update_or_create(
                vendedor=vendedor_selecionado,
                rifa=rifa_selecionada,
                defaults={'comissao_fixa': comissao, 'ativo': True}
            )
            messages.success(request, f"O vendedor foi associado à rifa '{rifa_selecionada.titulo}' com sucesso!")  # noqa: E501
            return redirect('gerenciar_vendedores')
    else:
        form = VendedorForm()

    return render(request, 'core/pages/gerenciar_vendedores.html', {
        'vendedores': vendedores,
        'form': form,
        'rifas': rifas
    })

# =====================================================================
# MODERAÇÃO DE COMENTÁRIOS (ORGANIZADOR)
# =====================================================================


@login_required
def moderar_comentarios(request):
    comentarios_pendentes = Comentario.objects.filter(rifa__autor=request.user, status='PENDENTE').order_by('data_criacao')  # noqa: E501
    return render(request, 'core/pages/moderar_comentarios.html', {'comentarios': comentarios_pendentes})  # noqa: E501


@login_required
def acao_comentario(request, comentario_id, acao):
    comentario = get_object_or_404(Comentario, id=comentario_id, rifa__autor=request.user)  # noqa: E501

    if acao == 'aprovar':
        comentario.status = 'APROVADO'
        messages.success(request, "Comentário aprovado! Ele agora é público na página da rifa.")  # noqa: E501
    elif acao == 'rejeitar':
        comentario.status = 'REJEITADO'
        messages.warning(request, "Comentário rejeitado e ocultado.")

    comentario.save()
    return redirect('moderar_comentarios')

# =====================================================================
# TRANSAÇÕES E CHECKOUT (COMPRADORES)
# =====================================================================


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
    compra = get_object_or_404(Compra, id=compra_id, comprador=request.user)
    numeros_vinculados = compra.numeros_alocados.all()

    if request.method == 'POST':
        form = CheckoutForm(request.POST, request.FILES, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, "Comprovante enviado com sucesso! O organizador avaliará em breve.")  # noqa: E501
            return redirect('detalhe_compra', compra_id=compra.id)
    else:
        form = CheckoutForm(instance=compra)

    return render(request, 'core/pages/detalhe_compra.html', {
        'compra': compra,
        'numeros': numeros_vinculados,
        'form': form
    })


@login_required
def cancelar_reserva(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id, comprador=request.user)

    if compra.status == 'PENDENTE':
        numeros = NumerosRifa.objects.filter(compra=compra)
        for n in numeros:
            n.status = 'DISPONIVEL'
            n.compra = None
            n.save()
        compra.delete()
        messages.info(request, "A reserva do número foi cancelada.")
    else:
        messages.error(request, "Não é possível cancelar uma cota que já está em análise ou paga.")  # noqa: E501

    return redirect('home')


@login_required
def painel_relatorios(request):
    # Filtra apenas as rifas criadas pelo organizador logado
    minhas_rifas = Rifa.objects.filter(autor=request.user)

    # 1. CÁLCULO FINANCEIRO CONSOLIDADO
    # Total Arrecadado: Compras com status 'PAGO'
    total_arrecadado = Compra.objects.filter(rifa__autor=request.user, status='PAGO').count() * 10.00   # noqa: E501
    # Substitua pelo campo real de valor se necessário
    # Pendente: Compras aguardando validação de PIX com comprovante enviado
    total_pendente = Compra.objects.filter(rifa__autor=request.user, status='PENDENTE').exclude(comprovante='').count() * 10.00  # noqa: E501
    # Inadimplência: Reservas expiradas (tempo esgotado sem pagamento)
    total_inadimplencia = Compra.objects.filter(rifa__autor=request.user, status='EXPIRADO').count() * 10.00  # noqa: E501

    # 2. DESEMPENHO DOS VENDEDORES
    vendedores_dados = []
    vendedores_vinculados = User.objects.filter(perfil__papel='VENDEDOR', perfil__organizador_vinculado=request.user)  # noqa: E501

    for vendedor in vendedores_vinculados:
        compras_vendedor = Compra.objects.filter(vendedor_associado=vendedor)
        pagas = compras_vendedor.filter(status='PAGO').count()
        pendentes = compras_vendedor.filter(status='PENDENTE').count()

        # Busca a comissão fixa configurada para o primeiro vínculo 
        # encontrado (ou 0.00)
        vinculo = VendedorRifa.objects.filter(vendedor=vendedor).first()
        comissao_unidade = vinculo.comissao_fixa if vinculo else 0.00
        comissao_estimada = pagas * comissao_unidade

        vendedores_dados.append({
            'username': vendedor.username,
            'vendas_pagas': pagas,
            'vendas_pendentes': pendentes,
            'comissao': comissao_estimada
        })

    return render(request, 'core/pages/painel_relatorios.html', {
        'rifas': minhas_rifas,
        'total_arrecadado': total_arrecadado,
        'total_pendente': total_pendente,
        'total_inadimplencia': total_inadimplencia,
        'vendedores': vendedores_dados
    })


@login_required
def exportar_csv(request, tipo):
    response = HttpResponse(content_type='text/csv; charset=utf-8')

    if tipo == 'financeiro':
        response['Content-Disposition'] = 'attachment; filename="relatorio_financeiro.csv"'  # noqa: E501
        writer = csv.writer(response)
        writer.writerow(['Métrica', 'Valor Estimado (R$)'])

        pagas = Compra.objects.filter(rifa__autor=request.user, status='PAGO').count() * 10.00  # noqa: E501
        pendentes = Compra.objects.filter(rifa__autor=request.user, status='PENDENTE').exclude(comprovante='').count() * 10.00  # noqa: E501
        expiradas = Compra.objects.filter(rifa__autor=request.user, status='EXPIRADO').count() * 10.00  # noqa: E501

        writer.writerow(['Total Arrecadado (Aprovados)', f"R$ {pagas:.2f}"])
        writer.writerow(['Total Pendente (Em Análise)', f"R$ {pendentes:.2f}"])
        writer.writerow(['Inadimplência (Expirados)', f"R$ {expiradas:.2f}"])

    elif tipo == 'vendedores':
        response['Content-Disposition'] = 'attachment; filename="desempenho_vendedores.csv"'  # noqa: E501
        writer = csv.writer(response)
        writer.writerow(['Vendedor', 'Cotas Pagas', 'Cotas Pendentes', 'Comissão Acumulada (R$)'])  # noqa: E501

        vendedores = User.objects.filter(perfil__papel='VENDEDOR', perfil__organizador_vinculado=request.user)  # noqa: E501
        for v in vendedores:
            compras = Compra.objects.filter(vendedor_associado=v)
            pagas = compras.filter(status='PAGO').count()
            pendentes = compras.filter(status='PENDENTE').count()
            vinculo = VendedorRifa.objects.filter(vendedor=v).first()
            comissao = pagas * (vinculo.comissao_fixa if vinculo else 0)

            writer.writerow([v.username, pagas, pendentes, f"R$ {comissao:.2f}"])  # noqa: E501

    return response
