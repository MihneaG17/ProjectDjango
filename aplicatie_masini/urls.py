from django.urls import path
from . import views
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap
from .models import Masina

info_masini= {
	'queryset': Masina.objects.all(),
	'date_field': 'data_adaugarii',
}

sitemap_masini= GenericSitemap(
	info_masini,
	priority=0.8,
	changefreq="monthly",
)

sitemaps= {
	'static': StaticViewSitemap,
	'masini': sitemap_masini,
}
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
	path("login", views.login_view, name="login"),
	path("logout", views.logout_view, name="logout"),
	path("profil", views.profil_view, name="profil"),
	path("change-password", views.change_password_view, name="change-password"),
	path("confirma-mail/<str:cod_confirmare>/", views.confirmare_succes, name="confirmare-succes"),
	path("interzis", views.eroare403, name="interzis"),
	path("adauga-produse", views.adauga_produse, name="adauga-produse"),
	path("oferta", views.pagina_oferta, name="oferta"),
	path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
 	path("locatii", views.afis_produse, name="locatii"),
]
