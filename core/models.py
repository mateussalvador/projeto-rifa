from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Rifa(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])  # noqa: E501
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rifas_criadas')  # noqa: E501
    cover = models.ImageField(upload_to='rifas/covers/%Y/%m/%d')
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rifas_venda')  # noqa: E501
    link_sorteio = models.URLField(null=True, blank=True)
    qtd_numeros = models.IntegerField(default=100)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_sorteio = models.DateTimeField(null=True, blank=True)
    finalizada = models.BooleanField(default=False)

    # Campos de Sorteio e Finalização (Sprints 11-12)
    numero_ganhador = models.IntegerField(null=True, blank=True)
    ganhador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rifas_ganhas')  # noqa: E501

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Gera automaticamente os números disponíveis 
            # vinculados à grade desta rifa
            NumerosRifa.objects.bulk_create([
                NumerosRifa(rifa=self, numero=i) for i in range(1, self.qtd_numeros + 1)  # noqa: E501
            ])


class Premio(models.Model):
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='premios')  # noqa: E501
    posicao = models.IntegerField(help_text="Ex: 1 para Primeiro Lugar")
    descricao = models.CharField(max_length=255)

    class Meta:
        ordering = ['posicao']

    def __str__(self):
        return f"{self.posicao}º Prêmio - {self.rifa.titulo}"


class Compra(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente de Pagamento'),
        ('PAGO', 'Aprovado / Pago'),
        ('EXPIRADO', 'Reserva Expirada'),
    )
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compras')  # noqa: E501
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='compras_rifa')  # noqa: E501
    vendedor_associado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas_intermediadas')  # noqa: E501
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE')  # noqa: E501
    data_compra = models.DateTimeField(auto_now_add=True)
    comprovante = models.ImageField(upload_to='comprovantes/%Y/%m/%d', null=True, blank=True)  # noqa: E501
    cpf = models.CharField(max_length=14, blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.comprador.username} ({self.status})"


class NumerosRifa(models.Model):
    STATUS_NUMERO = (
        ('DISPONIVEL', 'Disponível'),
        ('RESERVADO', 'Reservado'),
        ('PAGO', 'Pago'),
    )
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='grade_numeros')  # noqa: E501
    numero = models.IntegerField()
    status = models.CharField(max_length=15, choices=STATUS_NUMERO, default='DISPONIVEL')  # noqa: E501
    compra = models.ForeignKey(Compra, on_delete=models.SET_NULL, null=True, blank=True, related_name='numeros_alocados')  # noqa: E501

    class Meta:
        unique_together = ('rifa', 'numero')
        ordering = ['numero']

    def __str__(self):
        return f"Nº {self.numero} - {self.rifa.titulo} [{self.status}]"
