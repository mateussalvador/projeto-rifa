from django.urls import path

from . import views

urlpatterns = [
    path('', views.home),
    path('rifas/<int:id>', views.rifas, name='rifas'),
]
