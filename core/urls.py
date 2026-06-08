from django.urls import path
from . import views
from .models import Rifa

urlpatterns = [
    path('', views.home),
    path('sobre/', views.sobre),
]