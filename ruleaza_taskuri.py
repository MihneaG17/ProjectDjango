import schedule
import time
import django
import os
import sys
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'magazinmasini.settings')
django.setup()

from aplicatie_masini import tasks

def run_scheduler():
    k=getattr(settings, 'K_TIMP_STERGERE', 2)
    zi=getattr(settings, 'Z_SAPTAMANA', 'miercuri').lower()
    ora=getattr(settings, 'O_ORA','12:00')
    m_minute=getattr(settings, 'M', 60)
    z2=getattr(settings, 'Z2', 'vineri').lower()
    o2=getattr(settings, 'O2', '18:00')
    
    schedule.every(k).minutes.do(tasks.sterge_utilizatori_neconfirmati)
    
    zile_dict={
        'luni': schedule.every().monday,
        'marti': schedule.every().tuesday,
        'miercuri': schedule.every().wednesday,
        'joi': schedule.every().thursday,
        'vineri': schedule.every().friday,
        'sambata': schedule.every().saturday,
        'duminica': schedule.every().sunday,
    }
    
    task_zi=zile_dict.get(zi)
    if task_zi:
        task_zi.at(ora).do(tasks.trimite_newsletter)
    
    schedule.every(m_minute).minutes.do(tasks.curatare_logari_nereusite)
    
    task_suplimentar_zi=zile_dict.get(z2)
    if task_suplimentar_zi:
        task_suplimentar_zi.at(o2).do(tasks.raport_admin)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("Scheduler oprit manual.")
        sys.exit()

