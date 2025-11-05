from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, datetime
import locale
from . import middleware
from .models import Locatie, Masina, Marca, CategorieMasina, Serviciu, Accesoriu

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
    #return HttpResponse(f"""
    #                 <html>
    #                    <head>
    #                    <title>Magazin masini</title>
    #                 </head>
    #                 <body>
    #                    <h1>Informatii despre server </h1>
    #                    <p>{afis_data(data_param)}</p>
    #                    {param_section}
    #                 </body>
    #                 </html>
    #                 """)

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
    return render(request,"aplicatie_masini/index.html",
        {
            "titlu_tab":"Magazin de masini",
            "banner_text":"Cele mai bune masini la un click distanta",
            "ip_client":request.META.get('REMOTE_ADDR',''),
        }
    )

def despre(request):
    return render(request, "aplicatie_masini/despre.html",
                  {
                      "ip_client":request.META.get('REMOTE_ADDR',''),
                  }
        )

def in_lucru(request):
    return render(request, "aplicatie_masini/in_lucru.html",
                  {
                      "ip_client":request.META.get('REMOTE_ADDR',''),
                  }
        )

def log_view(request):
    return render(request, "aplicatie_masini/in_lucru.html",
                  {
                      "ip_client":request.META.get('REMOTE_ADDR',''),
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

def produse(request): 
    nrPagina=request.GET.get("pagina")
    if not nrPagina:
        nrPagina=1
    try:
        nrPagina=int(nrPagina)
    except (ValueError, TypeError):
        return HttpResponse("Eroare: parametrul 'pagina' nu a primit o valoare numerica")
    
    masini = Masina.objects.all()
    paginator = Paginator(masini, 10)
    mesajEroare = None
    try:
        obPagina = paginator.page(nrPagina)
    except EmptyPage:
        obPagina=None
        mesajEroare="Nu mai sunt produse"
    return render(request, 'aplicatie_masini/produse.html', 
                    {
                        'pagina': obPagina,
                        'eroare': mesajEroare,
                        'ip_client':request.META.get('REMOTE_ADDR',''),
                    }
                  )

def detalii_masina(request, id):
    mesajEroare=None
    try:
        masina = Masina.objects.get(pk=id)
        return render(request, 'aplicatie_masini/detalii_masina.html', 
            {
            'masina': masina,
            'eroare': mesajEroare
            }
        )
    except Masina.DoesNotExist:
        mesajEroare="Masina pe care incerci sa o accesezi nu exista in baza de date"
        masina=None
        return render(request, 'aplicatie_masini/detalii_masina.html', 
            {
            'masina': masina,
            'eroare': mesajEroare
            }
        )
    

from .forms import ContactForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():  
            nume = form.cleaned_data['nume']
            email = form.cleaned_data['email']
            mesaj = form.cleaned_data['mesaj']
            #procesarea datelor
            return redirect('mesaj_trimis')
    else:
        form = ContactForm()
    return render(request, 'aplicatie_exemplu/contact.html', {'form': form})
