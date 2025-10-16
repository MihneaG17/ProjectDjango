from django.shortcuts import render
from datetime import date, datetime
import locale
from . import middleware
locale.setlocale(locale.LC_TIME, 'romanian')

# Create your views here.
from django.http import HttpResponse
def index(request):
	return HttpResponse("Magazin de masini")

def info(request):
    keys = list(request.GET.keys())
    count = len(keys)
    if count > 0:
        nume_param = ", ".join(keys)
    else:
        nume_param = "niciun parametru"
    param_section = f"<h2>Parametri</h2><p>Numar parametri: {count}</p><p>Nume parametri: {nume_param}</p>"
    
    data_param = request.GET.get("data")
    return HttpResponse(f"""
                     <html>
                        <head>
                        <title>Magazin masini</title>
                     </head>
                     <body>
                        <h1>Informatii despre server </h1>
                        <p>{afis_data(data_param)}</p>
                        {param_section}
                     </body>
                     </html>
                     """)

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
            for idx, log in enumerate(logs):
                lid = log.get("id")
                try:
                    lid_int=int(lid)
                except ValueError:
                    lid_int = idx+1
                
                if lid_int == id_cautat:
                    html.append(
                        f'<p>Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip", "")} - Time: {log.get("time")}</p>'
                    )
                    found = True
                    break
            if not found:
                html.append(f'<p>(Nu exista accesare cu id={id_cautat})</p>')
        return HttpResponse("".join(html))
    
    #ultimele
    if ultimele_param is None:
        for log in middleware.LOGS:
            html.append(f'<p> Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip")} - Time: {log.get("time")} </p>')
        return HttpResponse("".join(html))
    try:
        n=int(ultimele_param)
    except ValueError:
        return HttpResponse("Eroare: parametrul 'ultimele' nu a primit o valoare numerica")
    
    if n<=0:
        return HttpResponse("Eroare: parametrul 'ultimele' trebuie sa aiba o valoare pozitiva")
    
    total = len(middleware.LOGS)
    if n>total:
        for log in middleware.LOGS:
            html.append(f'<p> Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip")} - Time: {log.get("time")} </p>')
        html.append(f'<p>Exista doar {total} accesari fata de {n} cerute</p>')
        return HttpResponse("".join(html))
    
    ultimele_accesari = middleware.LOGS[-n:]
    for log in ultimele_accesari:
        html.append(f'<p> Path: {log.get("path")} - Method: {log.get("method")} - IP: {log.get("ip")} - Time: {log.get("time")} </p>')
    
    return HttpResponse("".join(html))
                


