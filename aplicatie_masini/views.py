from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import Permission
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail, mail_admins
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.db import models
from django.db.models import Case, When, Value, IntegerField
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime, timedelta
import locale
import json
import os
import time
import unicodedata
from . import middleware
from .models import Locatie, Masina, Marca, CategorieMasina, Serviciu, Accesoriu, CustomUser, IncercareLogare, Comanda, ItemComanda
from .forms import MasinaFilterForm, ContactForm, CustomUserCreationForm, CustomAuthenticationForm, FormularAdaugareProdus
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
locale.setlocale(locale.LC_TIME, 'romanian')

# Create your views here.
from django.http import HttpResponse

logger=logging.getLogger('django')

def info(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if not request.user.groups.filter(name='Administratori_site').exists():
        nr_accesari=request.session.get('contor_403',0)
        nr_accesari+=1
        request.session['contor_403']=nr_accesari
        flag_rosu=False
        mesaj_atentionare=""
        
        if nr_accesari>settings.N_MAX_403:
            flag_rosu=True
            mesaj_atentionare=f"Ai incercat sa accesezi resurse interzise de {nr_accesari}"
        return HttpResponseForbidden(render(request, 'aplicatie_masini/eroare403.html', {
            'titlu': 'Eroare accesare pagină info',
            'mesaj_personalizat': 'Nu ai voie să accesezi această pagină',
            'mesaj_atentionare': mesaj_atentionare,
            'nr_accesari': nr_accesari,
            'flag_rosu': flag_rosu,
            'toate_categoriile': categorii_meniu,
            'ip_client': request.META.get('REMOTE_ADDR',''),
        }))
        
    keys = list(request.GET.keys())
    count = len(keys)
    if count > 0:
        nume_param = ", ".join(keys)
    else:
        nume_param = "niciun parametru"
    param_section = f"<h2>Parametri</h2><p>Numar parametri: {count}</p><p>Nume parametri: {nume_param}</p>"
    
    data_param = request.GET.get("data")
    data_info = afis_data(data_param)
    
    continut_info = f"""
                    <h1>Informatii despre server </h1>
                        <p>{data_info}</p>
                        {param_section}
                    """
    return render(request, 'aplicatie_masini/info.html', {
        'continut_info': continut_info,
        'toate_categoriile': categorii_meniu,
        'ip_client': request.META.get('REMOTE_ADDR',''),
        } )

def afis_data(data):
    if(not data):
        return ""
    else:
        today = datetime.now()
        if(data == "zi"):
            return f"{today.day} {today.strftime("%B").capitalize()} {today.year}"
        elif(data == 'timp'):
            return f"{today.hour}:{today.minute}:{today.second}"
        else:
            return f"{today.strftime("%A").capitalize()}, {today.day} {today.strftime("%B").capitalize()} {today.year}"


class Accesare:
    id_cnt=0
    def __init__(self, ip_client, url, data):
        Accesare.id_cnt+=1
        self.id=Accesare.id_cnt
        self.ip_client=ip_client
        self.url=url
        self.data=data
    
    def lista_parametri(self, request):
        lista_finala = []
        for cheie in request.GET.keys():
            valori = request.GET.getlist(cheie)
            if not valori:
                valoare = None
            elif len(valori)==1:
                valoare = valori[0]
            else:
                valoare = valori
            lista_finala.append((cheie, valoare))
        return lista_finala
    
    def get_url(self, request):
        full_url = request.get_full_path()
        return full_url
    
    def format_data(self, format_data):
        if(isinstance(self.data, str)):
            data_obj = datetime.strptime(self.data, "%d-%m-%Y %H:%M:%S")
        else:
            data_obj = self.data
        return data_obj.strftime(format_data)
    
    def pagina(self):
        string=self.url
        if '?' in string:
            string=string.split('?', 1)[0]
        if not string.startswith('/'):
            string = string + '/'
        return string or '/'
        


def exemplu_view(request):
    acces1 = Accesare(request.META.get('REMOTE_ADDR', '0.0.0.0'),
                        request.get_full_path(),
                        datetime.now())
    
    param_lst = acces1.lista_parametri(request)
    full = acces1.get_url(request)
    data_fmt=acces1.format_data("%A, %d %B %Y %H:%M:%S")
    pagina=acces1.pagina()
    
    html=f"""
        <h1>Test Accesare</h1>
        <p>id: {acces1.id}</p>
        <p>ip: {acces1.ip_client}</p>
        <p>pagina: {pagina}</p>
        <p>url: {full}</p>
        <p>data: {data_fmt}</p>
        <p>parametri: {param_lst}</p>
    """
    return HttpResponse(html)
        
    
def afis_template(request):
    return render(request,"aplicatie_masini/exemplu.html",
        {
            "titlu_tab":"Titlu fereastra",
            "titlu_articol":"Titlu afisat",
            "continut_articol":"Continut text"
        }
    )

#functie pentru log-uri
def afis_log(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if not request.user.groups.filter(name='Administratori_site').exists():
        nr_accesari=request.session.get('contor_403',0)
        nr_accesari+=1
        request.session['contor_403']=nr_accesari
        flag_rosu=False
        mesaj_atentionare=""
        
        if nr_accesari>settings.N_MAX_403:
            flag_rosu=True
            mesaj_atentionare=f"Ai incercat sa accesezi resurse interzise de {nr_accesari}"
        return HttpResponseForbidden(render(request, 'aplicatie_masini/eroare403.html', {
            'titlu': 'Eroare accesare pagină log',
            'mesaj_personalizat': 'Nu ai voie să accesezi această pagină',
            'mesaj_atentionare': mesaj_atentionare,
            'nr_accesari': nr_accesari,
            'flag_rosu': flag_rosu,
            'toate_categoriile': categorii_meniu,
            'ip_client': request.META.get('REMOTE_ADDR',''),
        }))
    
    html = []
    
    ultimele_param = request.GET.get("ultimele")
    accesari_param = request.GET.get("accesari")
    dubluri_param = request.GET.get("dubluri")
    dubluri = dubluri_param in ("true", "TRUE")
    tabel_param = request.GET.get("tabel")
    
    logs = middleware.LOGS
    total=len(logs)
    
    #accesari
    if accesari_param=="nr":
        html.append(f"<h3>Numar total de accesari: {total}</h3>")
    
    if accesari_param=="detalii":
        html.append("<h3>Detalii accesari (data si ora):</h3>")
        html.append("<ul>")
        for log in logs:
            time = log.get("time")
            timestr=time.strftime("%Y-%m-%d %H:%M:%S")
            html.append(f"<li>{timestr}</li>")
        html.append("</ul>")
    
    iduri_val = request.GET.getlist("iduri")
    iduri_secventa = []
    if iduri_val:
        for chunk in iduri_val: #chunk reprezinta id-urile care sunt puse intr-o singura aparitie a parametrului, de exemplu: iduri=2,3&iduri=5,6 - chunk va fi ['2,3', '5,6']
            for val in chunk.split(","):
                val=val.strip()
                try:
                    id_int = int(val)
                except ValueError:
                    continue
                if not dubluri and id_int in iduri_secventa:
                    continue
                iduri_secventa.append(id_int)
    if iduri_secventa:
        for id_cautat in iduri_secventa:
            found=False
            for log in logs:
                lid_int = log.get("id")
                if lid_int == id_cautat:
                    html.append(f'<p>Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip", "")} - Time: {log.get("time")}</p>')
                    found=True
                    break
            if not found:
                html.append(f'<p>(Nu exista accesare cu id={id_cautat})</p>')
    
    #ultimele
    logs_to_display=logs
    if ultimele_param is None:
        for log in logs_to_display:
            html.append(f'<p> Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip")} - Time: {log.get("time")} </p>')
    else:
        try:
            n=int(ultimele_param)
        except (ValueError, TypeError):
            return HttpResponse("Eroare: parametrul 'ultimele' nu a primit o valoare numerica")
        
        if n<=0:
            return HttpResponse("Eroare: parametrul 'ultimele' trebuie sa aiba o valoare pozitiva")
        
        total = len(logs)
        if n>total:
            for log in logs_to_display:
                html.append(f'<p> Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip")} - Time: {log.get("time")} </p>')
            html.append(f'<p>Exista doar {total} accesari fata de {n} cerute</p>')
        else:
            logs_to_display = logs[-n:] #ultimele log-uri
            for log in logs_to_display:
                html.append(f'<p> Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip")} - Time: {log.get("time")} </p>')
    
    logs = logs_to_display
    
    #tabel
    if tabel_param == "tot":
        html.append("<table border='1' cellpadding='4' cellspacing='0'>")
        html.append("<tr><th>ID</th><th>Path</th><th>Method</th><th>IP</th><th>Time</th></tr>")
        for log in logs:
            time = log.get("time")
            timestr=time.strftime("%Y-%m-%d %H:%M:%S")
            html.append(f"<tr><td>{log.get('id')}</td><td>{log.get('path')}</td><td>{log.get('method')}</td><td>{log.get('ip')}</td><td>{timestr}</td></tr>")
    
    elif tabel_param is not None and tabel_param != "":
        tabel_categ=[]
        categorii=tabel_param.split(",")
        categorii_acceptate=['id', 'path', 'method', 'ip', 'time']
        for item in categorii:
            if item in categorii_acceptate:
                tabel_categ.append(item)
        
        if not tabel_categ:
            html.append("<p>Parametrul tabel nu contine coloane valide</p>")
        else:
            html.append("<table border='1' cellpadding='4' cellspacing='0'>")
            html.append("<tr>")
            for categ in tabel_categ:
                html.append(f"<th>{categ.capitalize()}</th>")
            html.append("</tr>")
            for log in logs:
                html.append("<tr>")
                for categ in tabel_categ:
                    html.append(f"<td>{log.get(categ)}</td>")
                html.append("</tr>")
            html.append("</table>")

    #lista pagini cel mai mult/cel mai putin accesate
    if logs:
        frecv= {}
        for log in logs:
            path = log.get("path", "/")
            path = path.split("?")[0]
            if path in frecv:
                frecv[path]+=1
            else:
                frecv[path]=1
        max_cnt=0
        min_cnt=None
        pagini_max=[]
        pagini_min=[]
        
        for path, count in frecv.items():
            if count>max_cnt:
                max_cnt=count
            if min_cnt is None or count<min_cnt:
                min_cnt=count
        
        for path, count in frecv.items():
            if count==max_cnt:
                pagini_max.append(path)
            if count==min_cnt:
                pagini_min.append(path)
        
        html.append("<h3>Statistici accesari: </h3>")
        html.append("<p>Pagina/paginile cu cele mai multe accesari: " + ", ".join(pagini_max)+f"({max_cnt} accesari)</p>")
        html.append("<p>Pagina/paginile cu cele mai putine accesari: " + ", ".join(pagini_min)+f"({min_cnt} accesari)</p>")
    continut_log = "".join(html)
    return render(request, 'aplicatie_masini/log.html', {
        'continut_log': continut_log,
        'toate_categoriile': categorii_meniu,
        'ip_client': request.META.get('REMOTE_ADDR',''),
        })       


#view-uri pentru template rendering
def index(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    masini_recente=Masina.objects.all().order_by("-id")[:3]
    return render(request,"aplicatie_masini/index.html",
        {
            "titlu_tab":"Magazin de mașini",
            "banner_text":"Cele mai bune mașini la un click distanță",
            "ip_client":request.META.get('REMOTE_ADDR',''),
            "toate_categoriile":categorii_meniu,
            "oferte_recente": masini_recente,
        }
    )

def despre(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    return render(request, "aplicatie_masini/despre.html",
                  {
                      "ip_client":request.META.get('REMOTE_ADDR',''),
                      "toate_categoriile":categorii_meniu,
                  }
        )

def in_lucru(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    return render(request, "aplicatie_masini/in_lucru.html",
                  {
                      "ip_client":request.META.get('REMOTE_ADDR',''),
                      "toate_categoriile":categorii_meniu,
                  }
        )

def log_view(request):
    return render(request, "aplicatie_masini/in_lucru.html",
                  {
                      "ip_client":request.META.get('REMOTE_ADDR',''),
                  }
        )

def afis_produse(request):
    locatii = Locatie.object.all()
    return render(request, "aplicatie_masini/locatii.html",
                  {
                      "locatii": locatii[0],
                      "nr_locatii": len(locatii),
                  }
        )

def produse(request, nume_categorie=None): 
    logger.debug(f"Accesare pagina de produse. Parametrii GET {request.GET}") #debug 1- pentru a vedea parametrii get (filtrele) aplicate
    messages.debug(request, f"Filtre aplicate: {request.GET.urlencode()}") #mesaj debug 1
    
    param_sortare=request.GET.get("sort")
    nrPagina=request.GET.get("pagina")
    elemente_pe_pagina=9
    
    if not nrPagina:
        nrPagina=1
    try:
        nrPagina=int(nrPagina)
    except (ValueError, TypeError):
        return HttpResponse("Eroare: parametrul 'pagina' nu a primit o valoare numerică")
    
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    categorie_curenta=None
    mesajEroare=None
    mesajPaginare=None
    form=MasinaFilterForm(request.GET)
    
    if nume_categorie:
        try:
            categorie_curenta=CategorieMasina.objects.get(nume_categorie=nume_categorie)
            masini=Masina.objects.filter(categorie=categorie_curenta)
        except CategorieMasina.DoesNotExist:
            mesajEroare="Categoria introdusă nu există."
            masini = Masina.objects.none()
    else:
        masini = Masina.objects.all()
    
    form.categorie_de_verificat=categorie_curenta
    if form.is_valid():
        cd = form.cleaned_data

        if categorie_curenta:
            masini = masini.filter(categorie=categorie_curenta)
        elif cd.get('categorie'):
            masini = masini.filter(categorie=cd.get('categorie'))
            
        if cd.get('model'):
            masini = masini.filter(model__icontains=cd.get('model'))
        if cd.get('marca'):
            masini = masini.filter(marca=cd.get('marca'))
        if cd.get('tip_combustibil'):
            masini = masini.filter(tip_combustibil=cd.get('tip_combustibil'))
        if cd.get('an_fabricatie'):
            masini = masini.filter(an_fabricatie=cd.get('an_fabricatie'))
        if cd.get('pret_min'):
            masini = masini.filter(pret_masina__gte=cd.get('pret_min'))
        if cd.get('pret_max'):
            masini = masini.filter(pret_masina__lte=cd.get('pret_max'))
        if cd.get('kilometraj_max'):
            masini = masini.filter(kilometraj__lte=cd.get('kilometraj_max'))
        if cd.get('elemente_afisate'):
            elemente_pe_pagina = cd.get('elemente_afisate')
            mesajPaginare = "În urma repaginării este posibil ca unele produse deja vizualizate să fie din nou afișate sau altele să fie sărite"
    
    if not mesajEroare:
        if param_sortare=='a':
            masini=masini.annotate(
                stoc_disponibil=Case(
                    When(stoc__gt=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-stoc_disponibil', 'pret_masina')
        elif param_sortare=='d':
            masini=masini.annotate(
                stoc_disponibil=Case(
                    When(stoc__gt=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-stoc_disponibil', '-pret_masina')
        else:
            masini=masini.annotate(
                stoc_disponibil=Case(
                    When(stoc__gt=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-stoc_disponibil', '-data_adaugarii')
    
    if not masini.exists() and not mesajEroare:
        mesajEroare="Nu au fost găsite produse care să corespundă filtrelor"
        obPagina=None
    else:   
        paginator = Paginator(masini, elemente_pe_pagina)
        try:
            obPagina = paginator.page(nrPagina)
        except EmptyPage:
            obPagina=None
            if not mesajEroare:
                mesajEroare="Nu au fost găsite produse"
    
    param_fara_sort=""
    for cheie in request.GET:
        if cheie!="sort":
            valoare=request.GET[cheie]
            param_fara_sort+="&"+cheie+"="+valoare 
    
    string_reset=""
    if param_sortare:
        string_reset=f"?sort={param_sortare}"
            
    return render(request, 'aplicatie_masini/produse.html', 
                    {
                        'pagina': obPagina,
                        'eroare': mesajEroare,
                        'mesaj_paginare': mesajPaginare,
                        'param_sortare': param_sortare,
                        'toate_categoriile': categorii_meniu,
                        'categorie_curenta': categorie_curenta,
                        'form': form,
                        'request_get_string': request.GET.urlencode(),
                        'params_fara_sort': param_fara_sort,
                        'string_reset': string_reset,
                        'ip_client':request.META.get('REMOTE_ADDR',''),
                    }
                  )

def detalii_masina(request, id):
    mesajEroare=None
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    try:
        masina = Masina.objects.get(pk=id)
        messages.debug(request, f"Vizualizare obiect Masina ID={id} - {masina.model}") #mesaj debug 2
        return render(request, 'aplicatie_masini/detalii_masina.html', 
            {
            'masina': masina,
            'eroare': mesajEroare,
            'toate_categoriile': categorii_meniu
            }
        )
    except Masina.DoesNotExist:
        mesajEroare="Masina pe care incerci sa o accesezi nu exista in baza de date"
        masina=None
        return render(request, 'aplicatie_masini/detalii_masina.html', 
            {
            'masina': masina,
            'eroare': mesajEroare,
            'toate_categoriile': categorii_meniu,
            }
        )

def contact(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if request.method== 'POST':
        logger.debug(f"Datele brute primite din formularul de contact: {request.POST}") #debug 2
        
        form=ContactForm(request.POST)
        if form.is_valid():
            date_mesaj=form.cleaned_data
            date_mesaj.pop("confirmare_email", None)
            date_mesaj["ip_adresa"]=request.META.get('REMOTE_ADDR','')
            date_mesaj["data_ora_primire"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            timestamp=int(time.time())
            nume_fisier=f"mesaj_{timestamp}"
            if date_mesaj.get("urgent")==True:
                nume_fisier+="_urgent"
            nume_fisier+=".json"
            
            try:
                folder_mesaje=os.path.join(settings.BASE_DIR, 'mesaje')
                os.makedirs(folder_mesaje,exist_ok=True)
                cale_fisier=os.path.join(folder_mesaje,nume_fisier)
                with open(cale_fisier, "w") as f:
                #with open("Z:/nuexista/fisier.json", "w") as f: #---test pentru trimitere mail-uri admini
                    json.dump(date_mesaj,f,indent=4,default=str)
                return render(request, 'aplicatie_masini/contact.html', {
                    "form": ContactForm(),
                    "mesaj_succes": "Mesajul a fost trimis cu succes",
                    'ip_client': request.META.get('REMOTE_ADDR',''),
                    'toate_categoriile': categorii_meniu,
                })
            except Exception as e:
                
                logger.error(f"Eroare la scrierea fisierului JSON: {e}") #error 1
                
                subiect_eroare=f"Eroare la salvarea mesajului de contact: {nume_fisier}"
                mesaj_text=f"A aparut o eroare la scrierea mesajelor pe disc: {e}"
                mesaj_html = f"""
                    <h1>Atentie administratori!</h1>
                    <p>Sistemul nu a putut salva un mesaj de contact primit.</p>
                    <p><strong>Detalii eroare:</strong></p>
                    <div style="background-color: red; color: white; padding: 15px; border-radius: 5px;">
                        {e}
                    </div>
                    <p>Va rugam sa verificati spatiul pe disc si permisiunile folderului.</p>
                """
                mail_admins(
                    subject=subiect_eroare,
                    message=mesaj_text,
                    html_message=mesaj_html
                )
                messages.error(request, "Ne pare rău, a apărut o eroare tehnică și mesajul nu a putut fi trimis. Administratorii au fost notificați.") #mesaj eroare 1
                
                return render(request, 'aplicatie_masini/contact.html', {
                    "form": form,
                    'toate_categoriile': categorii_meniu,
                })
        else:
            logger.warning(f"Formular de contact invalid. Erori: {form.errors}") #warning 2
            messages.warning(request, "Formularul conține erori. Verifică datele introduse.") #mesaj warning 2
    else:
        form=ContactForm()
    return render(request, 'aplicatie_masini/contact.html', {
        'ip_client': request.META.get('REMOTE_ADDR',''),
        'toate_categoriile': categorii_meniu,
        'form': form,
    })

def inregistrare(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if request.method=="POST":
        form=CustomUserCreationForm(request.POST)
        if form.is_valid():
            user=form.save(commit=False)
            user.cod=get_random_string(length=15)
            user.save()

            logger.info(f"Utilizator nou inregistrat - {user.username}") #info 1
            
            #cale_relativa=f"/aplicatie_masini/confirmare-succes/{user.cod}"
            cale_relativa = reverse("confirmare-succes", args=[user.cod])
            link_complet=request.build_absolute_uri(cale_relativa)
            """
            current_site=Site.objects.get_current()
            domeniu=current_site.domain
            cale_logo=settings.STATIC_URL + "aplicatie_masini/imagini/logo-site.png"
            url_logo=f"http://{domeniu}{cale_logo}"
            """
            cale_logo=settings.STATIC_URL + "aplicatie_masini/imagini/logo-site.png"
            url_logo=request.build_absolute_uri(cale_logo)
            
            context={
                'nume': user.last_name,
                'prenume': user.first_name,
                'username': user.username,
                'link_confirmare': link_complet,
                'url_logo': url_logo,
                }
            html_content=render_to_string('aplicatie_masini/email-confirmare.html', context)
            mesaj=f"Salut {user.username}, confirma contul aici: {link_complet}"
            
            try:
                send_mail(
                    subject='Confirmare cont - Magazin masini',
                    message=mesaj,
                    html_message=html_content,
                    from_email='mihneadjango@gmail.com',
                    recipient_list=['mihneadjango@gmail.com', user.email],
                    fail_silently=False,
                )
                messages.success(request, f"Contul a fost creat! Un email de confirmare a fost trimis la {user.email}.")
            except Exception as e:
                logger.critical(f"Eroare critica: Nu s-a putut trimite email de confirmare pentru userul '{user.username}'. Eroare: {e}") #critical 2
                messages.error(request, f"Contul a fost creat, dar nu am putut trimite emailul. Eroare: {e}")
            return redirect('index')
    else:
        form=CustomUserCreationForm()
    return render(request, 'aplicatie_masini/inregistrare.html', {
        'form': form,
        'toate_categoriile': categorii_meniu,
    })

def login_view(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if request.method=="POST":
        form=CustomAuthenticationForm(data=request.POST, request=request)
        if form.is_valid():
            user=form.get_user()
            
            if user.blocat:
                messages.error(request, "Contul tău a fost blocat. Contactează un administrator.") #mesaj eroare 2
                return redirect('login')
            
            if user.email_confirmat:
                login(request, user)
                
                logger.info(f"Utilizator logat cu succes - {user.username}") #info 2
                
                if not form.cleaned_data.get('ramane_logat'):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(24*60*60)
                return redirect('profil')
            else:
                logger.warning(f"Tentativa de login cu email neconfirmat: {user.username}") #warning 1
                
                messages.warning(request, "Contul există, dar trebuie să îți confirmi adresa de email pentru a te putea loga") #mesaj warning 1
                #messages.error(request, "Te rugăm să îți confirmi adresa de mail pentru a te putea loga.")
        else:
            ip=request.META.get('REMOTE_ADDR')
            user_incercat=request.POST.get('username')
            IncercareLogare.objects.create(username_folosit=user_incercat, ip_folosit=ip) #adaugare inregistrare in baza de date direct din cod
            
            timp_acum=timezone.now()
            limita_timp=timp_acum-timedelta(minutes=2)
            nr_incercari=IncercareLogare.objects.filter(ip_folosit=ip, data_incercare__gte=limita_timp).count()
            if nr_incercari>=3:
                logger.critical(f"Posibil atac: 3 logari esuate de la adresa {ip}") #critical 1
                
                subiect="Logari suspecte"
                mesaj_text=f"Utilizatorul {user_incercat} a incercat sa se logheze de pe ip-ul {ip} de prea multe ori în mai puțin de 2 minute."
                mesaj_html=f"""
                    <h1 style="color: red">{subiect}</h1>
                    <p>Username incercat: {user_incercat}</p>
                    <p>IP suspect: {ip}</p>
                    <p>Numar de incercari: {nr_incercari}</p>
                """
                mail_admins(
                    subject=subiect,
                    message=mesaj_text,
                    html_message=mesaj_html
                )
    else:
        form=CustomAuthenticationForm()
    return render(request, 'aplicatie_masini/login.html', {
        'form': form,
        'toate_categoriile': categorii_meniu,
    })

def logout_view(request):
    if request.user.is_authenticated:
        try:
            permisiune=Permission.objects.get(codename="vizualizare_oferta")
            request.user.user_permissions.remove(permisiune)
        except Permission.DoesNotExist:
            pass
    logout(request)
    messages.info(request, "Te-ai delogat cu succes! Te mai așteptăm!") #mesaj info 1
    return redirect('index')

def profil_view(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    return render(request, 'aplicatie_masini/profil.html', {
        'toate_categoriile': categorii_meniu,
    })

def change_password_view(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if request.method=="POST":
        form=PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Parola a fost actualizata') #mesaj succes 2
            return redirect('index')
        else:
            messages.error(request, 'Exista erori')
    else:
        form=PasswordChangeForm(user=request.user)
        
    return render(request, 'aplicatie_masini/change-password.html', {
        'form': form,
        'toate_categoriile': categorii_meniu,
    })
    
def confirmare_succes(request, cod_confirmare):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    try:
        user=CustomUser.objects.get(cod=cod_confirmare)
        user.email_confirmat=True
        user.save()
        messages.success(request, "Contul a fost confirmat cu succes!")
    except CustomUser.DoesNotExist:
        logger.error(f"Incercare confirmare cu cod invalid: {cod_confirmare}") #error 2
        messages.error(request, "Link-ul de confirmare este invalid sau a fost deja folosit.")
    except Exception as e:
        messages.error(request, "A apărut o eroare la confirmarea contului.")
    return render(request, 'aplicatie_masini/confirmare-succes.html', {
        'toate_categoriile': categorii_meniu,
        'ip_client': request.META.get('REMOTE_ADDR',''),
    })

def adauga_produse(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if not request.user.has_perm('aplicatie_masini.add_masina'):
        nr_accesari=request.session.get('contor_403',0)
        nr_accesari+=1
        request.session['contor_403']=nr_accesari
        flag_rosu=False
        mesaj_atentionare=""
        
        if nr_accesari>settings.N_MAX_403:
            flag_rosu=True
            mesaj_atentionare=f"Ai incercat sa accesezi resurse interzise de {nr_accesari}"
        return HttpResponseForbidden(render(request, 'aplicatie_masini/eroare403.html', {
            'titlu': 'Eroare adăugare produse',
            'mesaj_personalizat': 'Nu ai voie să adaugi mașini',
            'mesaj_atentionare': mesaj_atentionare,
            'nr_accesari': nr_accesari,
            'flag_rosu': flag_rosu,
            'toate_categoriile': categorii_meniu,
            'ip_client': request.META.get('REMOTE_ADDR',''),
        }))

    if request.method=="POST":
        form=FormularAdaugareProdus(request.POST, request.FILES) 
        if form.is_valid():
            pret_initial=form.cleaned_data['pret_achizitie']
            procent=form.cleaned_data['procent_adaos']
            
            produs=form.save(commit=False)
            pret=pret_initial + (procent*pret_initial)/100
            produs.pret_masina=pret
            
            produs.save()
            form.save_m2m()
            
            messages.success(request, "Produsul a fost adăugat cu succes în baza de date") #mesaj succes 1
            return redirect('adauga-produse')
    else:
        form=FormularAdaugareProdus()
        
    return render(request, 'aplicatie_masini/adauga-produse.html', {
        'toate_categoriile': categorii_meniu,
        'form': form,
        'ip_client': request.META.get('REMOTE_ADDR',''),
    })

def eroare403(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    
    nr_accesari=request.session.get('contor_403',0)
    nr_accesari+=1
    request.session['contor_403']=nr_accesari
    flag_rosu=False
    mesaj_atentionare=""
    
    if nr_accesari>settings.N_MAX_403:
        flag_rosu=True
        mesaj_atentionare=f"Ai incercat sa accesezi resurse interzise de {nr_accesari}"
    
    titlu=""
    mesaj_personalizat="Ai încercat să accesezi o resursă interzisă"
    return render(request, 'aplicatie_masini/eroare403.html', {
        'toate_categoriile': categorii_meniu,
        'titlu': titlu,
        'mesaj_personalizat': mesaj_personalizat,
        'mesaj_atentionare': mesaj_atentionare,
        'nr_accesari': nr_accesari,
        'flag_rosu': flag_rosu,
        'ip_client': request.META.get('REMOTE_ADDR',''),
    })

def pagina_oferta(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    if request.user.is_authenticated and request.GET.get('sursa')=="banner":
        try:
            permisiune=Permission.objects.get(codename="vizualizare_oferta")
            request.user.user_permissions.add(permisiune)
            messages.info(request, "Felicitări! Ai deblocat oferta specială prin accesarea bannerului.") #mesaj info 2 
        except Permission.DoesNotExist:
            pass


def cos_virtual(request):
    """
    Pagina coșului virtual - gestionează și afișează produsele adiauste în coș
    """
    categorii_meniu = CategorieMasina.objects.all().order_by('nume_categorie')
    return render(request, 'aplicatie_masini/cos_virtual.html', {
        'toate_categoriile': categorii_meniu,
    })

    if not request.user.has_perm('aplicatie_masini.vizualizare_oferta'):
        nr_accesari=request.session.get('contor_403',0)
        nr_accesari+=1
        request.session['contor_403']=nr_accesari
        flag_rosu=False
        mesaj_atentionare=""
        
        if nr_accesari>settings.N_MAX_403:
            flag_rosu=True
            mesaj_atentionare=f"Ai incercat sa accesezi resurse interzise de {nr_accesari}"
        return HttpResponseForbidden(render(request, 'aplicatie_masini/eroare403.html', {
            'titlu': 'Eroare afișare ofertă',
            'mesaj_personalizat': 'Nu ai voie să vizualizezi oferta',
            'mesaj_atentionare': mesaj_atentionare,
            'nr_accesari': nr_accesari,
            'flag_rosu': flag_rosu,
            'toate_categoriile': categorii_meniu,
            'ip_client': request.META.get('REMOTE_ADDR',''),
        }))
    return render(request, 'aplicatie_masini/pagina-oferta.html', {
        'toate_categoriile': categorii_meniu,
        'ip_client': request.META.get('REMOTE_ADDR',''),
    })


def elimina_diacritice(text):
    """
    Elimina diacriticele dintr-un text
    """
    if not text:
        return text
    nfd_form = unicodedata.normalize('NFD', str(text))
    return ''.join(char for char in nfd_form if unicodedata.category(char) != 'Mn')


def genereaza_factura_pdf(comanda, request=None):

    folder_facturi = os.path.join(settings.BASE_DIR, 'temporar-facturi', comanda.utilizator.username)
    os.makedirs(folder_facturi, exist_ok=True)
    
    timestamp = int(time.time())
    cale_fisier = os.path.join(folder_facturi, f'factura-{timestamp}.pdf')
    
    doc = SimpleDocTemplate(cale_fisier, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    style_titlu = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f1f1f'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderPadding=5,
        borderColor=colors.HexColor('#4CAF50'),
        borderWidth=1,
        backColor=colors.HexColor('#f0f8f0')
    )
    
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8
    )

    story.append(Paragraph('FACTURA DE VANZARE', style_titlu))
    story.append(Spacer(1, 0.2*inch))

    data_formatata = comanda.data_comanda.strftime('%d.%m.%Y %H:%M')
    info_comanda = f"""
    <b>Numar Factura:</b> #{comanda.id} | <b>Data:</b> {data_formatata}<br/>
    """
    story.append(Paragraph(info_comanda, style_normal))
    story.append(Spacer(1, 0.15*inch))

    admin_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'admin@magazinmasini.ro'
    story.append(Paragraph('INFORMATII VANZATOR', style_heading))
    vanzator_info = f"""
    <b>Magazin Masini</b><br/>
    Contact: {admin_email}<br/>
    """
    story.append(Paragraph(vanzator_info, style_normal))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph('INFORMATII CLIENT', style_heading))
    
    client_first = elimina_diacritice(comanda.utilizator.first_name or 'N/A')
    client_last = elimina_diacritice(comanda.utilizator.last_name or 'N/A')
    client_email = elimina_diacritice(comanda.utilizator.email)
    client_telefon = elimina_diacritice(comanda.utilizator.telefon or 'N/A')
    client_strada = elimina_diacritice(comanda.utilizator.strada or 'N/A')
    client_oras = elimina_diacritice(comanda.utilizator.oras or 'N/A')
    client_cod = elimina_diacritice(comanda.utilizator.cod_postal or 'N/A')
    
    client_info = f"""
    <b>Nume:</b> {client_first}<br/>
    <b>Prenume:</b> {client_last}<br/>
    <b>E-mail:</b> {client_email}<br/>
    <b>Telefon:</b> {client_telefon}<br/>
    <b>Adresa:</b> {client_strada}, {client_oras} {client_cod}<br/>
    """
    story.append(Paragraph(client_info, style_normal))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph('PRODUSELE COMANDATE', style_heading))

    table_data = [
        ['Produs', 'Categoria', 'Combustibil', 'Cantitate', 'Pret Unitar', 'Subtotal']
    ]
    
    items = comanda.itemcomanda_set.all()
    for item in items:
        masina = item.masina
        produs_text = elimina_diacritice(f"{masina.marca.nume_marca} {masina.model} ({masina.an_fabricatie})")
        categorie_text = elimina_diacritice(masina.categorie.nume_categorie)
        combustibil_text = elimina_diacritice(masina.get_tip_combustibil_display())
        
        tabla_row = [
            produs_text,
            categorie_text,
            combustibil_text,
            str(item.cantitate),
            f"{item.pret_unitar:.2f} EUR",
            f"{item.subtotal:.2f} EUR"
        ]
        table_data.append(tabla_row)

    t = Table(table_data, colWidths=[2*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph('REZUMAT FACTURII', style_heading))
    
    total_produse = sum(item.cantitate for item in items)
    total_pret = comanda.pret_total
    
    rezumat_text = f"""
    <b>Total Produse:</b> {total_produse} unitati<br/>
    <b style="font-size: 14px; color: #4CAF50;">TOTAL DE PLATA: {total_pret:.2f} EUR</b><br/>
    <br/>
    """
    story.append(Paragraph(rezumat_text, style_normal))

    if request:
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph('<b>Detalii Produse:</b>', style_heading))
        
        links_text = ""
        for item in items:
            masina = item.masina
            produs_link = elimina_diacritice(f"{masina.marca.nume_marca} {masina.model}")
            url_produs = request.build_absolute_uri(reverse('detalii_masina', kwargs={'id': masina.id}))
            links_text += f"* {produs_link}: {url_produs}<br/>"
        
        story.append(Paragraph(links_text, style_normal))

    story.append(Spacer(1, 0.2*inch))
    footer_text = f"""
    <i>Pentru orice intrebari sau probleme, contactati: {admin_email}</i><br/>
    <i>Factura generata automat pe {data_formatata}</i>
    """
    story.append(Paragraph(footer_text, style_normal))

    doc.build(story)
    
    return cale_fisier


@require_POST
def checkout(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Trebuie să fii autentificat'}, status=401)
    
    try:
        data = json.loads(request.body)
        cart = data.get('cart', {})
        
        if not cart:
            return JsonResponse({'success': False, 'error': 'Coșul este gol'})
        
        comanda = Comanda.objects.create(
            utilizator=request.user,
            pret_total=0
        )
        
        total_pret = 0

        for product_id_str, product_data in cart.items():
            product_id = int(product_id_str)
            try:
                masina = Masina.objects.get(pk=product_id)
                cantitate = int(product_data.get('quantity', 1))
                pret_unitar = float(product_data.get('price', masina.pret_masina))

                if cantitate > masina.stoc:
                    return JsonResponse({
                        'success': False,
                        'error': f'Stocul insuficient pentru {masina.marca.nume_marca} {masina.model}. Disponibil: {masina.stoc}, Solicitat: {cantitate}'
                    })

                masina.stoc -= cantitate
                masina.save()

                item = ItemComanda.objects.create(
                    comanda=comanda,
                    masina=masina,
                    cantitate=cantitate,
                    pret_unitar=pret_unitar
                )
                
                total_pret += item.subtotal
            
            except Masina.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Produsul {product_id} nu mai există'})

        comanda.pret_total = total_pret
        comanda.save()

        cale_factura = genereaza_factura_pdf(comanda, request)

        trimite_email_factura(request.user, comanda, cale_factura)
        
        return JsonResponse({
            'success': True,
            'message': f'✓ Comandă plasat cu succes! Factură trimisă la {request.user.email}',
            'order_id': comanda.id
        })
    
    except Exception as e:
        logger.error(f"Eroare checkout: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Eroare: {str(e)}'})


def trimite_email_factura(utilizator, comanda, cale_factura):
    try:
        subiect = f'Factură Comandă #{comanda.id} - Magazin Mașini'

        with open(cale_factura, 'rb') as attachment:
            content_pdf = attachment.read()

        mesaj_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #4CAF50;">Mulțumim pentru comandă!</h2>
                <p>Bună {utilizator.first_name or utilizator.username},</p>
                <p>Comanda ta a fost înregistrată cu succes.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Detalii Comandă:</strong></p>
                    <p>Număr Comandă: <strong>#{comanda.id}</strong></p>
                    <p>Data: <strong>{comanda.data_comanda.strftime('%d.%m.%Y %H:%M')}</strong></p>
                    <p>Total: <strong>{comanda.pret_total:.2f} EUR</strong></p>
                </div>
                
                <p>Factura detaliată este atașată în acest email.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p><small>Dacă ai întrebări, te rog contactează-ne la {settings.DEFAULT_FROM_EMAIL}</small></p>
                </div>
            </body>
        </html>
        """
        
        from django.core.mail import EmailMessage
        email = EmailMessage(
            subject=subiect,
            body=mesaj_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[utilizator.email],
        )
        email.content_subtype = 'html'

        email.attach(f'factura-{comanda.id}.pdf', content_pdf, 'application/pdf')
        
        email.send()
        
    except Exception as e:
        logger.error(f"Eroare trimitere email: {str(e)}")