from django.shortcuts import render
from datetime import date, datetime
import locale
locale.setlocale(locale.LC_TIME, 'romanian')

# Create your views here.
from django.http import HttpResponse
def index(request):
	return HttpResponse("Magazin de masini")

def info(request):
    data_param = request.GET.get("data")
    #return exemplu_view(request)
    return HttpResponse(f"""
                     <html>
                        <head>
                        <title>Magazin masini</title>
                     </head>
                     <body>
                        <h1>Informatii despre server </h1>
                        <p>{afis_data(data_param)}</p>
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
