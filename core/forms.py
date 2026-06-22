from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError  # noqa
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Comentario, Compra, Rifa


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crie uma senha forte'})  # noqa: E501
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),  # noqa: E501
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),  # noqa: E501
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class VendedorForm(forms.ModelForm):
    telefone = forms.CharField(
        max_length=15, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'})  # noqa: E501
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: joaovendas'}),  # noqa: E501
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'joao@email.com'}),  # noqa: E501
        }


class RifaForm(forms.ModelForm):
    class Meta:
        model = Rifa
        fields = ['titulo', 'descricao', 'valor', 'cover', 'qtd_numeros', 'data_sorteio', 'link_sorteio']  # noqa: E501
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Rifa de um iPhone 15'}),  # noqa: E501
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detalhes do sorteio e regulamento...'}),  # noqa: E501
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),  # noqa: E501
            'cover': forms.FileInput(attrs={'class': 'form-control'}),
            'qtd_numeros': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_sorteio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),  # noqa: E501
            'link_sorteio': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/... (Opcional)'}),  # noqa: E501
        }

    def clean_data_sorteio(self):
        data_sorteio = self.cleaned_data.get('data_sorteio')
        if data_sorteio and data_sorteio < timezone.now():
            raise forms.ValidationError("A data do sorteio não pode ser no passado. Escolha uma data futura!")  # noqa: E501
        return data_sorteio


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['cpf', 'comprovante']
        widgets = {
            'comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cpf'].required = True
        self.fields['comprovante'].required = True

        self.fields['cpf'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '00000000000 (Apenas números)',
            'maxlength': '11',
            'pattern': r'^\d{11}$',
            'inputmode': 'numeric',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '');"
        })

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '').strip()

        if not cpf.isdigit():
            raise forms.ValidationError("O CPF deve conter apenas números.")
        if len(cpf) != 11:
            raise forms.ValidationError("O CPF deve ter exatamente 11 dígitos.")  # noqa: E501
        if cpf == cpf[0] * 11:
            raise forms.ValidationError("CPF inválido. Evite sequências repetidas.")  # noqa: E501

        return cpf


class CleanPasswordResetForm(PasswordResetForm):
    def save(self, domain_override=None, subject_template_name='registration/password_reset_subject.txt',  # noqa: E501
             email_template_name='registration/password_reset_email.html', use_https=False,  # noqa: E501
             token_generator=None, from_email=None, request=None, html_email_template_name=None,  # noqa: E501
             extra_email_context=None):

        if token_generator is None:
            token_generator = default_token_generator

        email_messages = []
        for user in self.get_users(self.cleaned_data["email"]):
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            context = {
                'email': user.email,
                'domain': domain_override or (request.get_host() if request else ''),  # noqa: E501
                'site_name': 'Rifando',
                'uid': uid,
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            if extra_email_context is not None:
                context.update(extra_email_context)

            try:
                subject = loader.render_to_string(subject_template_name, context)  # noqa: E501
                subject = ''.join(subject.splitlines())
            except loader.TemplateDoesNotExist:
                subject = f"Recuperação de senha - {context['site_name']}"

            link = f"{context['protocol']}://{context['domain']}/recuperar-senha/confirmar/{context['uid']}/{context['token']}/"  # noqa: E501
            
            body = (
                f"Olá {user.username},\n\n"
                f"Você solicitou a recuperação de senha para sua conta no Rifando.\n\n"  # noqa: E501
                f"Clique no link abaixo para definir uma nova senha:\n\n"
                f"{link}\n\n"
                f"Se você não solicitou isso, desconsidere este e-mail."
            )

            email_message = EmailMultiAlternatives(subject, body, from_email, [user.email])  # noqa: E501
            email_messages.append(email_message)

        for message in email_messages:
            message.send()


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['nome', 'email', 'texto']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome'}),  # noqa: E501
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Seu e-mail (não será publicado)'}),  # noqa: E501
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deixe uma mensagem, dúvida ou torcida...'}),  # noqa: E501
        }
