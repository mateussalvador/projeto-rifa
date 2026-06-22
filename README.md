# 🎟️ Rifando - Sistema de Gestão de Rifas Online

O **Rifando** é uma aplicação web desenvolvida em Python com o framework Django para a criação, venda e gerenciamento automatizado de rifas e sorteios baseados em cotas/números. 

O sistema foi desenhado para atender tanto o organizador da campanha quanto os compradores e vendedores parceiros (intermediadores), contando com rotinas automáticas de expiração de reservas e uma experiência visual fluida para a realização de sorteios em tempo real.

---

## 🚀 Funcionalidades Principais

### 👤 Autenticação & Usuários
* **Multi-papeis:** Suporte para Organizadores (Criadores), Vendedores Parceiros e Compradores comuns.
* Sistema seguro de cadastro, login e logout integrado ao `django.contrib.auth`.

### 🎯 Criação & Exibição de Campanhas
* Cadastro completo de rifas com título, descrição, valor por cota, imagem de capa (`ImageField`), quantidade total de números e prêmios múltiplos ordenados por posição.
* **Homepage Dinâmica:** Listagem de rifas com marcadores de status (`🟢 Aberta` / `🔒 Encerrada`) e exibição da data/hora oficial do sorteio.

### 🎟️ Grade de Números & Compra (Checkout)
* Geração automatizada da grade de números (`bulk_create`) no momento da criação da rifa.
* Seleção visual de cotas disponíveis.
* **Venda Direta ou por Intermediário:** O comprador pode selecionar um vendedor parceiro na cota ou optar por comprar diretamente pelo site (caso "caia de paraquedas").
* Fluxo de reserva com upload de comprovante de PIX e confirmação obrigatória de CPF.

### 🛡️ Validação & Segurança de Dados
* **Validação de CPF no Frontend:** Bloqueio em tempo real (`oninput` via Expressão Regular) impedindo o usuário de digitar letras, símbolos ou mais de 11 dígitos.
* **Validação de CPF no Backend:** Garante integridade antes de salvar a intenção de compra no banco de dados.

### 💼 Painel do Organizador & Moderação de Pagamentos
* **Central de Controle:** Área exclusiva para o organizador visualizar todas as suas campanhas criadas.
* **Validação de PIX:** Tela interna para auditoria de comprovantes enviados, exibindo o número da cota e o CPF do comprador. Permite aprovar (muda cota para `PAGO`) ou recusar (libera a cota para a grade).
* **Expiração Automática (24 horas):** Rotina inteligente integrada que identifica reservas pendentes com mais de 1 dia e as remove do banco, liberando os números automaticamente.

### 🎲 Sorteio Oficial com Animação Digital
* Execução do sorteio baseada exclusivamente nos números com status `PAGO`.
* **Sorteio Assíncrono (`Fetch API`):** O backend processa o vencedor em segundo plano enquanto o frontend executa uma animação de contagem regressiva e uma roleta de números girando em alta velocidade.
* **Fim Controlado:** A animação para **exatamente** no número sorteado, exibe os parabéns ao ganhador e segura a tela por 4 segundos antes de atualizar o status da campanha para `Encerrada`.
* **Link de Transmissão:** Permite ao organizador anexar o link do vídeo do sorteio (Ex: YouTube/Instagram) para auditoria pública dos compradores.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem Principal:** Python 3.13+
* **Framework Web:** Django 6.0+
* **Banco de Dados:** SQLite (Desenvolvimento/Ambiente TST)
* **Frontend:** HTML5, CSS3 (Design Responsivo) e JavaScript Assíncrono (Fetch API / ES6)

---

## 📦 Como Executar o Projeto Localmente

### 1. Clonar o Repositório
```bash
git clone https://github.com/mateussalvador/projeto_rifa.git
cd projeto_rifa
```

### 2. Configurar o Ambiente Virtual (venv)
- No Linux (Ubuntu):
```bash
python3 -m venv venv
source venv/bin/activate
```

- No Windows: 

No Linux (Ubuntu):
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```
- *(Nota: Certifique-se de que o `Pillow` está instalado para o suport a imagens).*

### 4. Executar as Migrações do Banco de Dados
```bash
python manage.py makemigrations core
python
```

### 5. Criar um Usuário Administrador
```bash
python manage.py createsuperuser
```

### 6. Iniciar o Servidor de Desenvolvimento
```bash
python manage.py runserver 8080
```

- O projeto estará acessível em: `http://localhost:8080/`

---

## 📂 Estrutura de Pastas Simplificada
```
projeto_rifa/
│
├── core/
│   ├── migrations/
│   ├── templates/core/
│   │   ├── pages/
│   │   │   ├── home.html
│   │   │   ├── rifa.html
│   │   │   ├── meu_painel.html
│   │   │   └── gerenciar_comprovantes.html
│   │   └── partials/
│   │       ├── header.html
│   │       └── lista_rifas.html
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── media/               # Destino dos covers de rifas e comprovantes PIX
├── projeto_rifa/        # Configurações do projeto (settings.py, urls.py)
├── manage.py
└── README.md
```

## Autor
- Mateus Salvador - Desenvolvedor do Projeto - https://github.com/mateussalvador
