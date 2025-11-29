from django.urls import path
from . import views
urlpatterns = [
	path("", views.index, name="index"),
	path("info", views.info, name="info"),
	path("exemplu", views.afis_template, name='exemplu'),
	path("log", views.afis_log, name="log"),
	path("produse", views.produse, name="produse"),
	path("categorii/<str:nume_categorie>", views.produse, name="produse_pe_categorie"),
 	path("masina/<int:id>", views.detalii_masina, name="detalii_masina"),
	path("despre", views.despre, name="despre"),
	path("cos_virtual", views.in_lucru, name="cos_virtual"),
	path("contact", views.contact, name="contact"),
	path("inregistrare", views.inregistrare, name="inregistrare"),
 	path("locatii", views.afis_produse, name="locatii"),
]
