from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import CleanPasswordResetForm

urlpatterns = [
    # Rotas de Navegação Geral e Autenticação Comum
    path('', views.home, name='home'),
    path('cadastro/', views.cadastrar_usuario, name='cadastro'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),

    # Rotas Relacionadas a Operações de Rifa
    path('rifas/<int:id>/', views.rifas, name='rifas'),
    path('rifas/criar/', views.criar_rifa, name='criar_rifa'),
    path('rifas/<int:rifa_id>/reservar/<int:numero>/', views.reservar_numero, name='reservar_numero'),  # noqa: E501

    # Rotas de Checkout e Cancelamento do Comprador
    path('compra/<int:compra_id>/', views.detalhe_compra, name='detalhe_compra'),  # noqa: E501
    path('compra/<int:compra_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),  # noqa: E501

    # Rotas de Gestão do Organizador (Painel, Moderação, Equipe e Sorteio)
    path('meu-painel/', views.meu_painel, name='meu_painel'),
    path('meu-painel/comprovantes/', views.gerenciar_comprovantes, name='gerenciar_comprovantes'),  # noqa: E501
    path('meu-painel/vendedores/', views.gerenciar_vendedores, name='gerenciar_vendedores'),  # noqa: E501
    path('rifas/<int:rifa_id>/sortear/', views.realizar_sorteio, name='realizar_sorteio'),  # noqa: E501
    path('compra/<int:compra_id>/aprovar/', views.aprovar_comprovante, name='aprovar_comprovante'),  # noqa: E501
    path('compra/<int:compra_id>/recusar/', views.recusar_comprovante, name='recusar_comprovante'),  # noqa: E501

    # Fluxo Seguro de Recuperação de Senha (django.contrib.auth)
    path('recuperar-senha/', 
         auth_views.PasswordResetView.as_view(
             template_name='core/pages/password_reset.html',
             form_class=CleanPasswordResetForm
         ),
         name='password_reset'),

    path('recuperar-senha/enviado/',  # noqa: E501
         auth_views.PasswordResetDoneView.as_view(template_name='core/pages/password_reset_done.html'),  # noqa: E501
         name='password_reset_done'),

    path('recuperar-senha/confirmar/<uidb64>/<token>/',  # noqa: E501
         auth_views.PasswordResetConfirmView.as_view(template_name='core/pages/password_reset_confirm.html'),  # noqa: E501
         name='password_reset_confirm'),

    path('recuperar-senha/sucesso/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='core/pages/password_reset_complete.html'),  # noqa: E501
         name='password_reset_complete'),
    path('meu-painel/comentarios/', views.moderar_comentarios, name='moderar_comentarios'),  # noqa: E501
    path('comentario/<int:comentario_id>/<str:acao>/', views.acao_comentario, name='acao_comentario'),  # noqa: E501
    # ... outras rotas de gestão ...
    path('meu-painel/relatorios/', views.painel_relatorios, name='painel_relatorios'),  # noqa: E501 
    path('meu-painel/relatorios/exportar/<str:tipo>/', views.exportar_csv, name='exportar_csv'),  # noqa: E501
]
