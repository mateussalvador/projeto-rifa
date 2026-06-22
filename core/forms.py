from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Compra, Rifa


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crie uma senha'})  # noqa: E501
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


class RifaForm(forms.ModelForm):
    class Meta:
        model = Rifa
        # Incluído o campo 'link_sorteio'
        fields = ['titulo', 'descricao', 'valor', 'cover', 'qtd_numeros', 'data_sorteio', 'link_sorteio']  # noqa: E501
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Rifa de um iPhone 15'}),  # noqa: E501
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detalhes do sorteio...'}),  # noqa: E501
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
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),  # noqa: E501
            'comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # Força a obrigatoriedade dos campos no nível do formulário Django
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cpf'].required = True
        self.fields['comprovante'].required = True
