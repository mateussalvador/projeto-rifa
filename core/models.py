from django.contrib.auth.models import User
from django.db import models


class Rifa(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rifas_criadas')  # noqa: E501
    cover = models.ImageField(upload_to='recipes/cover/%Y/%m/%d')
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rifas_vendidas')  # noqa: E501
    link_sorteio = models.URLField(null=True, blank=True)
    qtd_numeros = models.IntegerField(default=30)

    def __str__(self):
        return self.titulo
