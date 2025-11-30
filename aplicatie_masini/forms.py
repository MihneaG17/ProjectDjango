from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Marca, CategorieMasina, Masina, CustomUser
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
    
    def clean_categorie(self):
        categorie_trimisa=self.cleaned_data.get('categorie')
        categorie_de_verificat=getattr(self, 'categorie_de_verificat', None)
        if categorie_de_verificat:
            if categorie_trimisa and categorie_de_verificat.id!=categorie_trimisa.id:
                raise forms.ValidationError("Eroare de securitate: Nu aveți voie să modificați manual categoria curentă.")
        return categorie_trimisa
    
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
        raise forms.ValidationError("Mesajul trebuie sa aiba intre 5 si 100 de cuvinte")

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
        if value[0] not in ['1','2','5','6']:
            raise forms.ValidationError("CNP-ul trebuie sa inceapa cu 1, 2, 5 sau 6.")
        
        if value[0] in ['1','2']:
            an_prefix="19"
        elif value[0] in ['5','6']:
            an_prefix="20"
        else:
            an_prefix="19"  
            
        try:
            an_str=an_prefix+value[1:3]
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
    cnp=forms.CharField(max_length=13,min_length=13,required=False, label="CNP", validators=[validare_cnp_cifre, validare_cnp_corect])
    data_nasterii=forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, validators=[validare_varsta])
    email=forms.EmailField(required=True, validators=[validare_email_temporar])
    confirmare_email=forms.EmailField(required=True)
    tip_mesaj=forms.ChoiceField(choices=CONTACT_CHOICES, initial="neselectat", validators=[validare_tip_mesaj])
    subiect=forms.CharField(max_length=100, required=True, validators=[validare_fara_linkuri, validare_text_corect])
    minim_zile_asteptare=forms.IntegerField(required=True,label="Timp de asteptare (pentru review-uri/cereri minimul de zile de asteptare trebuie setat de la 4 incolo iar pentru reclamatii/programari/intrebari de la 2 incolo. Maximul e 30.)")
    mesaj=forms.CharField(widget=forms.Textarea, required=True, label="Mesaj (utilizatorul este rugat sa se semneze cu numele la finalul mesajului)", validators=[validare_lungime_mesaj, validare_lungime_cuvant, validare_fara_linkuri])
    
    def clean(self):
        cleaned_data=super().clean()
        self._validare_emailuri_identice(cleaned_data)
        self._validare_semnatura(cleaned_data)
        self._validare_zile_asteptare(cleaned_data)
        self._validare_cnp_data_nasterii(cleaned_data)
        
        data_nasterii=cleaned_data.get("data_nasterii")
        if data_nasterii:
            today=datetime.date.today()
            ani_persoana=today.year-data_nasterii.year
            luni_persoana=today.month-data_nasterii.month
            if (today.month, today.day)<(data_nasterii.month, data_nasterii.day):
                ani_persoana-=1
                luni_persoana+=12
            if today.day<data_nasterii.day:
                luni_persoana-=1
            if luni_persoana<0:
                luni_persoana+=12
            cleaned_data['varsta_formatata']=f"{ani_persoana} si {luni_persoana} luni"
            del cleaned_data['data_nasterii']
        
        mesaj=cleaned_data.get("mesaj")
        if mesaj:
            mesaj_curatat=" ".join(mesaj.split())
            if len(mesaj_curatat)>0:
                mesaj_curatat=mesaj_curatat[0].upper()+mesaj_curatat[1:]
            
            def litera_mare(match):
                text_gasit=match.group()
                return text_gasit.upper()  
            
            pattern=r"[?.!]\s*[a-z]"
            mesaj_curatat=re.sub(pattern,litera_mare,mesaj_curatat)
            
            cleaned_data["mesaj"]=mesaj_curatat    
        
        timp_asteptare=cleaned_data.get("minim_zile_asteptare")  
        tip_mesaj=cleaned_data.get("tip_mesaj") 
        urgent=False
        if tip_mesaj and timp_asteptare is not None:
            if tip_mesaj in ["review", "cerere"] and timp_asteptare==4:
                urgent=True
            elif tip_mesaj in ["reclamatie", "programare", "intrebare"] and timp_asteptare==2:
                urgent=True
        
        cleaned_data["urgent"]=urgent
        if urgent:
            subiect_vechi=cleaned_data.get("subiect")
            cleaned_data["subiect"]="URGENT"+subiect_vechi
            
        return cleaned_data
        
    
    def _validare_emailuri_identice(self, cleaned_data):
        email=cleaned_data.get("email")
        confirmare_email=cleaned_data.get("confirmare_email")
        if email!=confirmare_email:
            raise forms.ValidationError({"confirmare_email": "Adresele de email nu coincid"})
    
    def _validare_semnatura(self, cleaned_data):
        mesaj=cleaned_data.get("mesaj")
        nume=cleaned_data.get("nume")
        if not mesaj or not nume:
            return
        cuvinte=re.findall(r"\w+",mesaj)
        if not cuvinte:
            raise forms.ValidationError({"mesaj": "Mesajul nu conține cuvinte si lipseste semnatura."})
        ultimul_cuvant=cuvinte[-1].lower()
        if ultimul_cuvant!=nume.lower():
            raise forms.ValidationError({"mesaj": "Lipseste semnatura de la finalul mesajului"})
    
    def _validare_zile_asteptare(self, cleaned_data):
        zile_asteptare=cleaned_data.get("minim_zile_asteptare")
        tip_mesaj=cleaned_data.get("tip_mesaj")
        if zile_asteptare is None:
            return
        if zile_asteptare>30:
            raise forms.ValidationError({"minim_zile_asteptare": "Numarul de zile de asteptare nu poate fi mai mare de 30"})
        if tip_mesaj in ["review", "cerere"] and zile_asteptare <4:
            raise forms.ValidationError({"minim_zile_asteptare": "Numarul de zile de asteptare pentru acest tip de cerere trebuie sa fie de cel putin 4 zile"})
        elif tip_mesaj in ["reclamatie", "programare", "intrebare"] and zile_asteptare<2:
            raise forms.ValidationError({"minim_zile_asteptare": "Numarul de zile de asteptare pentru acest tip de cerere trebuie sa fie de cel putin 2 zile"})
    
    def _validare_cnp_data_nasterii(self, cleaned_data):
        cnp=cleaned_data.get("cnp")
        data_nasterii=cleaned_data.get("data_nasterii")
        if not cnp or not data_nasterii:
            return
        
        prima_cifra=cnp[0]
        if prima_cifra in ["1","2"]:
            an_prefix="19"
        elif prima_cifra in ["5","6"]:
            an_prefix="20"
        else:
            an_prefix="19"
        
        an_cnp=an_prefix+cnp[1:3]
        luna_cnp=cnp[3:5]
        zi_cnp=cnp[5:7]
        
        an_data=data_nasterii.year
        luna_data=data_nasterii.month
        zi_data=data_nasterii.day
        if int(an_cnp)!=an_data or int(luna_cnp)!=luna_data or int(zi_cnp)!=zi_data:
            raise forms.ValidationError({"cnp": "Datele din cnp nu corespund cu data nasterii"})
        
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields=("username", "email", "first_name", "last_name", "telefon", "tara", "judet", "oras", "strada", "cod_postal")
    
    def clean_telefon(self):
        telefon=self.cleaned_data.get('telefon')
        if telefon:
            if not re.match(r'^[\d\+\-\(\) ]+$', telefon):
                raise forms.ValidationError("Numărul de telefon conține și alte caractere care nu sunt numere")
        return telefon
    
    def clean_cod_postal(self):
        cod_postal=self.cleaned_data.get('cod_postal')
        if cod_postal:
            if not cod_postal.isdigit():
                raise forms.ValidationError("Codul poștal trebuie să conțină doar cifre")
        return cod_postal
    
    def clean(self):
        cleaned_data=super().clean()
        oras=cleaned_data.get('oras')
        judet=cleaned_data.get('judet')
        tara=cleaned_data.get('tara')
        if oras:
            for char in oras:
                if char.isdigit():
                    self.add_error('oras', "Numele orașului nu poate conține cifre")
        if judet:
            for char in judet:
                if char.isdigit():
                    self.add_error('judet', "Numele judetului nu poate conține cifre")
        if tara:
            for char in tara:
                if char.isdigit():
                    self.add_error('tara', "Numele țării nu poate conține cifre")
        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    ramane_logat=forms.BooleanField(required=False, initial=False, label="Ramaneti logat timp de o zi")
    
    def clean(self):
        cleaned_data=super().clean()
        ramane_logat=self.cleaned_data.get('ramane_logat')
        return cleaned_data