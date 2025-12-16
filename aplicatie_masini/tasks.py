from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import CustomUser, Masina, IncercareLogare
from django.template.loader import render_to_string
from django.core.mail import send_mail, mail_admins
import logging

logger=logging.getLogger('django')

def sterge_utilizatori_neconfirmati():
    minute_k=getattr(settings, 'K_TIMP_STERGERE', 2)
    timp_limita=timezone.now()-timedelta(minutes=minute_k)
    useri_de_sters=CustomUser.objects.filter(email_confirmat=False, date_joined__lt=timp_limita)
    
    for user in useri_de_sters:
        nume=user.username
        email=user.email
        
        user.delete()
        
        logger.warning(f"Task automat: User-ul {nume} ({email}) a fost sters deoarece nu si-a confirmat mail-ul")

def trimite_newsletter():
    minute_useri=getattr(settings, 'X_MINUTE', 10)
    
    interval_useri=timezone.now()-timedelta(minutes=minute_useri)
    useri=CustomUser.objects.filter(date_joined__lt=interval_useri)
    masini_noi=Masina.objects.order_by('-id')[:3]
    
    for user in useri:
        try:
            nume_utilizator=user.username
            context={
                'nume_utilizator': nume_utilizator,
                'masini_noi': masini_noi,
            }
            html_message=render_to_string('aplicatie_masini/newsletter.html', context)
        
        
            send_mail(
                subject="Newsletter Magazin Masini",
                message="Newsletter",
                html_message=html_message,
                from_email='mihneadjango@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Newsletter trimis cu succes catre {user.email}")
        except Exception as e:
            logger.error(f"Eroare: Nu s-a putut trimite newsletter pentru userul '{user.username}'. Eroare: {e}")

def curatare_logari_nereusite():
    timp_limita=timezone.now()-timedelta(hours=24)
    logari_vechi=IncercareLogare.objects.filter(data_incercare__lt=timp_limita)
    
    try:
        logari_vechi.delete()
        logger.info("Au fost sterse incercarile vechi de logare")
    except Exception as e:
        logger.warning(f"Nu au putut fi sterse logari vechi. Eroare: {e}")
        
def raport_admin():
    ultima_saptamana=timezone.now()-timedelta(weeks=1)
    
    useri_noi=CustomUser.objects.filter(date_joined__gte=ultima_saptamana)
    nr_useri_noi=useri_noi.count()
    
    masini_in_stoc=Masina.objects.filter(in_stoc=True)
    nr_masini_in_stoc=masini_in_stoc.count()
    
    masini_adaugate_recent=Masina.objects.filter(data_adaugarii__gte=ultima_saptamana)
    nr_masini_adaugate_recent=masini_adaugate_recent.count()
    
    try:
        subiect="Raport săptămânal site"
        mesaj_text="Iată raportul site-ului tău în ultima săptămână: "
        mesaj_html=f"""
            <h1>{subiect}</h1>
            <p>Numărul de useri noi înregistrați în ultima săptămână: {nr_useri_noi}</p>
            <p>Numărul de mașini disponibile în stoc: { nr_masini_in_stoc }</p>
            <p>Numărul de mașini adăugate în ultima săptămână: {nr_masini_adaugate_recent}</p>
        """
        mail_admins(
                    subject=subiect,
                    message=mesaj_text,
                    html_message=mesaj_html
                )
        logger.info('A fost trimis raportul saptamanal catre admini!')
    except Exception as e:
        logger.error(f'A aparut o eroare cu privire la trimiterea raportului saptamanal catre admini. Eroarea: {e}')