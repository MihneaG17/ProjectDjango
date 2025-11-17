from django import forms
from .models import Marca, CategorieMasina, Masina
import datetime
import re

class MasinaFilterForm(forms.Form):
    model=forms.CharField(max_length=100, required=False, label="Model")
    marca=forms.ModelChoiceField(queryset=Marca.objects.all(), required=False, label="Marca", empty_label="Toate marcile")
    categorie=forms.ModelChoiceField(queryset=CategorieMasina.objects.all(), required=False, label="Categorie", empty_label="Toate categoriile")
    tip_combustibil=forms.ChoiceField(choices=[('', 'Toate tipurile')] + Masina.TipCombustibil.choices, required=False, label="Combustibil")
    an_fabricatie=forms.IntegerField(required=False, label="An fabricatie")
    kilometraj_max=forms.IntegerField(required=False, label="Kilometraj maxim")
    pret_min=forms.DecimalField(max_digits=10,required=False, label="Pret minim")
    pret_max=forms.DecimalField(max_digits=10,required=False, label="Pret maxim")
    elemente_afisate=forms.IntegerField(required=False, label="Numar de produse afisate")
    
    def clean_an_fabricatie(self):
        an=self.cleaned_data.get('an_fabricatie')
        if an:
            anul_curent=datetime.date.today().year
            if an>anul_curent:
                raise forms.ValidationError("Anul fabricatiei nu poate fi in viitor")
        return an
    
    def clean_pret_min(self):
        pret_min=self.cleaned_data.get('pret_min')
        if pret_min is not None and pret_min<0:
            raise forms.ValidationError("Pretul minim nu poate fi un numar negativ")
        return pret_min

    def clean_elemente_afisate(self):
        elemente_afisate=self.cleaned_data.get('elemente_afisate')
        if elemente_afisate is not None and elemente_afisate<0:
            raise forms.ValidationError("Numarul de produse afisate nu poate fi negativ")
        return elemente_afisate
    
    def clean(self):
        cleaned_data=super().clean()
        pret_min=cleaned_data.get('pret_min')
        pret_max=cleaned_data.get('pret_max')
        if pret_min is not None and pret_max is not None:
            if pret_min>pret_max:
                raise forms.ValidationError("Pretul minim nu poate fi mai mare decat pretul maxim")
        return cleaned_data

def validare_varsta(value):
    today=datetime.date.today()
    varsta=today.year-value.year
    zi_nastere_trecuta=False
    if today.month>value.month:
        zi_nastere_trecuta=True
    elif today.month==value.month:
        if today.day>=value.day:
            zi_nastere_trecuta=True
    if not zi_nastere_trecuta:
        varsta-=1
    
    if varsta<18:
        raise forms.ValidationError("Expeditorul trebuie sa fie major")
    
def validare_lungime_mesaj(value):
    cuvinte=re.findall(r"\w+",value)
    if len(cuvinte)<5 or len(cuvinte)>100:
        raise forms.ValidationError("Mesajul trebuie sa aiba minim 5 cuvinte si maxim 100 de cuvinte")

def validare_lungime_cuvant(value):
    cuvinte=re.findall(r"\w+",value) 
    for cuvant in cuvinte:
        if len(cuvant)>15:
            raise forms.ValidationError("Lungimea unui cuvant nu trebuie sa depaseasca 15 caractere")

def validare_fara_linkuri(value):
    if "http://" in value or "https://" in value:
        raise forms.ValidationError("Textul nu poate contine link-uri")   
    
def validare_tip_mesaj(value):
    if value=="neselectat":
        raise forms.ValidationError("Va rugam sa selectati tipul mesajului")  

def validare_cnp_cifre(value):
    if value:
        if not value.isdigit():
            raise forms.ValidationError("CNP-ul trebuie sa contina doar cifre")

def validare_cnp_corect(value):
    if value:
        if value.startswith("1") or value.startswith("2"):
            an_prefix="19"
        else:
            raise forms.ValidationError("CNP-ul nu este valid")    
        try:
            an_str=value[1:3]
            luna_str=value[3:5]
            zi_str=value[5:7]
            datetime.date(year=int(an_str), month=int(luna_str), day=int(zi_str))
        except ValueError:
            raise forms.ValidationError("Data nasterii din CNP nu este valida")

def validare_email_temporar(value):
    if "guerillamail.com" in value.lower() or "yopmail.com" in value.lower():
        raise forms.ValidationError("Email-ul introdus este unul temporar")

def validare_text_corect(value):
    if not value:
        return value
    if not value[0].isupper():
        raise forms.ValidationError("Textul trebuie sa inceapa cu litera mare")
    for char in value:
        if not (char.isalpha() or char.isspace() or char=="-"):
            raise forms.ValidationError(f"Caracterul {char} nu este permis")
    return value
    
def validare_nume_prenume(value):
    if not value:
        return value
    if not value[0].isupper():
        raise forms.ValidationError("Numele trebuie sa inceapa cu litera mare")
    for i in range(1,len(value)):
        char_curent=value[i]
        char_anterior=value[i-1]
        if char_anterior==" " or char_anterior=="-":
            if not char_curent.isupper():
                raise forms.ValidationError("Prenumele trebuie sa inceapa cu litera mare")
    return value
    
CONTACT_CHOICES = (
    ("neselectat", "Neselectat"),
    ("reclamatie", "Reclamatie"),
    ("intrebare", "Intrebare"),
    ("review", "Review"),
    ("cerere", "Cerere"),
    ("programare", "Programare"),
)
class ContactForm(forms.Form):
    nume=forms.CharField(max_length=10, required=True, validators=[validare_text_corect,validare_nume_prenume])
    prenume=forms.CharField(max_length=10, required=False, validators=[validare_text_corect,validare_nume_prenume])
    cnp=forms.CharField(max_length=13,min_length=13,required=False, validators=[validare_cnp_cifre, validare_cnp_corect])
    data_nasterii=forms.DateField(required=True, validators=[validare_varsta])
    email=forms.EmailField(required=True, validators=[validare_email_temporar])
    confirmare_email=forms.EmailField(required=True)
    tip_mesaj=forms.ChoiceField(choices=CONTACT_CHOICES, default="neselectat", validators=[validare_tip_mesaj])
    subiect=forms.CharField(max_length=100, required=True, validators=[validare_fara_linkuri, validare_text_corect])
    minim_zile_asteptare=forms.IntegerField(required=True,label="Pentru review-uri/cereri minimul de zile de asteptare trebuie setat de la 4 incolo iar pentru cereri/intrebari de la 2 incolo. Maximul e 30.")
    mesaj=forms.CharField(widget=forms.Textarea, label='Mesaj', required=True, label="Utilizatorul este rugat sa se semneze la finalul mesajului.", validators=[validare_lungime_mesaj, validare_lungime_cuvant, validare_fara_linkuri])