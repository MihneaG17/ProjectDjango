from django import forms
from .models import Marca, CategorieMasina, Masina

class MasinaFilterForm(forms.Form):
    model=forms.CharField(max_length=100, required=False, label="Model")
    marca=forms.ModelChoiceField(queryset=Marca.objects.all(), required=False, label="Marca", empty_label="Toate marcile")
    categorie=forms.ModelChoiceField(queryset=CategorieMasina.objects.all(), required=False, label="Categorie", empty_label="Toate categoriile")
    tip_combustibil=forms.ChoiceField(choices=[('', 'Toate Tipurile')] + Masina.TipCombustibil.choices, required=False, label="Combustibil")
    an_fabricatie=forms.IntegerField(required=False, label="An fabricatie")
    kilometraj_max=forms.IntegerField(required=False, label="Kilometraj maxim")
    pret_min=forms.DecimalField(max_digits=10,required=False, label="Pret minim")
    pret_max=forms.DecimalField(max_digits=10,required=False, label="Pret maxim")
