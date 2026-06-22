from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Compra, NumerosRifa  # noqa


class Command(BaseCommand):
    help = 'Busca e libera reservas pendentes expiradas com mais de 24h'

    def handle(self, *args, **options):
        # Define o limite de 24 horas atrás
        tempo_limite = timezone.now() - timedelta(days=1)

        # Filtra compras PENDENTES que não enviaram 
        # comprovante e passaram do prazo
        compras_expiradas = Compra.objects.filter(
            status='PENDENTE', 
            data_compra__lt=tempo_limite,
            comprovante=''
        )

        quantidade = compras_expiradas.count()

        for compra in compras_expiradas:
            # Libera todas as cotas associadas a esta transação
            numeros_vinculados = compra.numeros_alocados.all()
            for numero_rifa in numeros_vinculados:
                numero_rifa.status = 'DISPONIVEL'
                numero_rifa.compra = None
                numero_rifa.save()

            compra.status = 'EXPIRADO'
            compra.save()

        if quantidade > 0:
            self.stdout.write(self.style.SUCCESS(f'{quantidade} reserva(s) expirada(s) foram limpas com sucesso!'))  # noqa: E501
        else:
            self.stdout.write(self.style.NOTICE('Nenhuma reserva expirada encontrada nesta rodada.'))  # noqa: E501
