import random

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Rifa


class Command(BaseCommand):
    help = 'Realiza o sorteio automático de rifas que atingiram o prazo'

    def handle(self, *args, **options):
        agora = timezone.now()

        # Filtra rifas não finalizadas onde a data do sorteio já passou
        rifas_para_sortear = Rifa.objects.filter(finalizada=False, data_sorteio__lte=agora)  # noqa: E501

        for rifa in rifas_para_sortear:
            numeros_pagos = rifa.grade_numeros.filter(status='PAGO')

            if not numeros_pagos.exists():
                # Se não houver vendas pagas, o sistema adia
                # o sorteio em 24h para evitar travamento
                rifa.data_sorteio = agora + timezone.timedelta(days=1)
                rifa.save()
                self.stdout.write(self.style.WARNING(f'Rifa "{rifa.titulo}" sem números pagos. Sorteio adiado em 24h.'))  # noqa: E501
                continue

            # Realiza a apuração aleatória
            numero_sorteado = random.choice(numeros_pagos)
            rifa.numero_ganhador = numero_sorteado.numero
            rifa.ganhador = numero_sorteado.compra.comprador
            rifa.finalizada = True
            rifa.save()

            # Dispara e-mail de premiação para o ganhador
            if rifa.ganhador.email:
                assunto = f"🎉 Sorteio Concluído! Você ganhou a rifa: {rifa.titulo}"  # noqa: E501
                mensagem = (
                    f"Olá, {rifa.ganhador.username}!\n\n"
                    f"O sorteio automático da campanha '{rifa.titulo}' foi realizado pelo sistema.\n\n"  # noqa: E501
                    f"Seu número da cota ({rifa.numero_ganhador}) foi o sorteado! Entre em contato com o organizador para receber seu prêmio."  # noqa: E501
                )
                send_mail(assunto, mensagem, None, [rifa.ganhador.email])

            self.stdout.write(self.style.SUCCESS(f'Rifa "{rifa.titulo}" sorteada com sucesso! Ganhador: {rifa.ganhador.username}'))  # noqa: E501
