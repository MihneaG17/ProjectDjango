from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, datetime
import locale
from . import middleware
from .models import Locatie, Masina, Marca, CategorieMasina, Serviciu, Accesoriu
from .forms import MasinaFilterForm

locale.setlocale(locale.LC_TIME, 'romanian')

# Create your views here.
from django.http import HttpResponse

def info(request):
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
                        <p>{afis_data(data_param)}</p>
                        {param_section}
                    """
    return render(request, 'aplicatie_masini/info.html', {'continut_info': continut_info} )

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
    return render(request, 'aplicatie_masini/log.html', {'continut_log': continut_log})    
    # return HttpResponse("".join(html))      


#view-uri pentru template rendering
def index(request):
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    return render(request,"aplicatie_masini/index.html",
        {
            "titlu_tab":"Magazin de masini",
            "banner_text":"Cele mai bune masini la un click distanta",
            "ip_client":request.META.get('REMOTE_ADDR',''),
            "toate_categoriile":categorii_meniu,
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
    param_sortare=request.GET.get("sort")
    nrPagina=request.GET.get("pagina")
    elemente_paginare_str=request.GET.get("elemente_afisate")
    
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
    
    if request.GET:
        if request.GET.get("model"):
            masini=masini.filter(model__icontains=request.GET.get("model"))
        if request.GET.get("marca"):
            masini=masini.filter(marca__id=request.GET.get("marca"))
        if request.GET.get("categorie"):
            masini=masini.filter(categorie__id=request.GET.get("categorie"))
        if request.GET.get("tip_combustibil"):
            masini=masini.filter(tip_combustibil=request.GET.get("tip_combustibil"))
        if request.GET.get("an_fabricatie"):
            masini=masini.filter(an_fabricatie=request.GET.get("an_fabricatie"))
        if request.GET.get("pret_min"):
            masini=masini.filter(pret_masina__gte=request.GET.get("pret_min"))
        if request.GET.get("pret_max"):
            masini=masini.filter(pret_masina__lte=request.GET.get("pret_max"))
        if request.GET.get("kilometraj_max"):
            masini=masini.filter(kilometraj__lte=request.GET.get("kilometraj_max"))
    
    if not mesajEroare:
        if param_sortare=='a':
            masini=masini.order_by('pret_masina')
        elif param_sortare=='d':
            masini=masini.order_by('-pret_masina')
        else:
            masini=masini.order_by('-data_adaugarii') #implicit dupa data adaugarii
    
    if not masini.exists() and not mesajEroare:
        mesajEroare="Nu au fost găsite produse care să corespundă filtrelor"
        obPagina=None
    else: 
        elemente_pe_pagina_int=10
        if elemente_paginare_str:
            try:
                elemente_pe_pagina_int=int(elemente_paginare_str)
                if elemente_pe_pagina_int<0:
                    elemente_pe_pagina_int=10
                mesajPaginare="În urma repaginării este posibil ca unele produse deja vizualizate să fie din nou afișate sau altele să fie sărite"
            except ValueError:
                mesajPaginare="Valoarea introdusă nu este de tip întreg"    
        paginator = Paginator(masini, elemente_pe_pagina_int)
        try:
            obPagina = paginator.page(nrPagina)
        except EmptyPage:
            obPagina=None
            if not mesajEroare:
                mesajEroare="Nu au fost găsite produse"
    
    if form.is_valid():
        cd=form.cleaned_data
        if categorie_curenta:
            masini=masini.filter(categorie=categorie_curenta)
        elif cd.get('categorie'):
            masini=masini.filter(categorie=cd.get('categorie'))
            
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
                        'ip_client':request.META.get('REMOTE_ADDR',''),
                    }
                  )

def detalii_masina(request, id):
    mesajEroare=None
    categorii_meniu=CategorieMasina.objects.all().order_by('nume_categorie')
    try:
        masina = Masina.objects.get(pk=id)
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
    return render(request, 'aplicatie_masini/contact.html', {
        'ip_client': request.META.get('REMOTE_ADDR',''),
        'toate_categoriile': categorii_meniu,
    })
