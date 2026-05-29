import secrets

numeros_comprados = list(range(1, 51))

numero_ganhador = secrets.choice(numeros_comprados)

print(f'O número sorteado foi o {numero_ganhador}')