from django.db import models
from django.contrib.auth.models import User

class Rifa(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits = 5, decimal_places=2)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='recipes/cover/%Y/%m/%d')

    def __str__(self):
        return self.titulo



