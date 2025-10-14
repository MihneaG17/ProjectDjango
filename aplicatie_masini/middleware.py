class Procesare: #MiddlewareNou
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # cod de procesare a cererii ....      
        #putem trimite date către funcția de vizualizare; le setăm ca proprietăți în request     
        request.proprietate_noua=17       
        # se apelează (indirect) funcția de vizualizare (din views.py)
        response = self.get_response(request)      

        # putem adauga un header HTTP pentru toate răspunsurile
        response['header_nou'] = 'valoare'
        # aici putem modifica chiar conținutul răspunsului
        # verificăm tipul de conținut folosind headerul HTTP Content-Type
        # motivul fiind că putem transmite și alte resurse (imagini, css etc.), nu doar fișiere html
        if response.has_header('Content-Type') and 'text/html' in response['Content-Type']:
           
            # obținem conținutul
            # (response.content este memorat ca bytes, deci îl transformăm în string)
            content = response.content.decode('utf-8')
           
            # Modificăm conținutul
           # new_content = content.replace(
            #    '</body>',
            #    '<div>Continut suplimentar</div></body>'
            #)
           
            # Suprascriem conținutul răspunsului
            #response.content = new_content.encode('utf-8')
           
            # Actualizăm lungimea conținutului (obligatoriu, fiind header HTTP)
            #response['Content-Length'] = len(response.content)
       
        return response       
