from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class PerfilUsuario(models.Model):
    PAPEIS_CHOICES = (
        ('ORGANIZADOR', 'Organizador'),
        ('VENDEDOR', 'Vendedor Parceiro'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')  # noqa: E501
    papel = models.CharField(max_length=15, choices=PAPEIS_CHOICES, default='ORGANIZADOR')  # noqa: E501
    # Se for vendedor, a qual organizador ele pertence?
    organizador_vinculado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='meus_vendedores')  # noqa: E501
    telefone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_papel_display()}"


class VendedorRifa(models.Model):
    """
    Associação Many-to-Many: Quais rifas o vendedor tem permissão para vender, 
    e qual a comissão fixa combinada para aquela campanha específica.
    """
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rifas_permitidas')  # noqa: E501
    rifa = models.ForeignKey('Rifa', on_delete=models.CASCADE, related_name='vendedores_associados')  # noqa: E501
    comissao_fixa = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Valor fixo ganho por cada número pago")  # noqa: E501
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('vendedor', 'rifa')
        # Impede que o organizador vincule o
        # mesmo vendedor duas vezes na mesma rifa

    def __str__(self):
        return f"{self.vendedor.username} -> {self.rifa.titulo} (R$ {self.comissao_fixa})"  # noqa: E501


@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def salvar_perfil_usuario(sender, instance, **kwargs):
    instance.perfil.save()


class Comentario(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente de Moderação'),
        ('APROVADO', 'Aprovado e Público'),
        ('REJEITADO', 'Rejeitado / Oculto'),
    )
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='comentarios')  # noqa: E501
    nome = models.CharField(max_length=100)
    email = models.EmailField(help_text="O e-mail não será exibido publicamente.")  # noqa: E501
    texto = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE')  # noqa: E501
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentário de {self.nome} ({self.get_status_display()})"