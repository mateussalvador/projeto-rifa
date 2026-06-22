from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('rifas/<int:id>/', views.rifas, name='rifas'),
    path('rifas/criar/', views.criar_rifa, name='criar_rifa'),
    path('rifas/<int:rifa_id>/reservar/<int:numero>/', views.reservar_numero, name='reservar_numero'),  # noqa: E501
    path('compra/<int:compra_id>/', views.detalhe_compra, name='detalhe_compra'),  # noqa: E501
    path('compra/<int:compra_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),  # noqa: E501
    path('cadastro/', views.cadastrar_usuario, name='cadastro'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('meu-painel/', views.meu_painel, name='meu_painel'),
    path('rifas/<int:rifa_id>/sortear/', views.realizar_sorteio, name='realizar_sorteio'),  # noqa: E501
    path('gerenciar-comprovantes/', views.gerenciar_comprovantes, name='gerenciar_comprovantes'),  # noqa: E501
    path('compra/<int:compra_id>/aprovar/', views.aprovar_comprovante, name='aprovar_comprovante'),  # noqa: E501
    path('compra/<int:compra_id>/recusar/', views.recusar_comprovante, name='recusar_comprovante'),  # noqa: E501
]
