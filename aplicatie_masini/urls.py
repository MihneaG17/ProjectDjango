from django.urls import path
from . import views
urlpatterns = [
	path("", views.index, name="index"),
	path("info", views.info, name="info"),
	path("exemplu", views.afis_template, name='exemplu'),
	path("log", views.afis_log, name="log"),
	path("produse", views.in_lucru, name="produse"),
	path("despre", views.despre, name="despre"),
	path("cos_virtual", views.in_lucru, name="cos_virtual"),
	path("contact", views.in_lucru, name="contact"),
 	path("locatii", views.afis_produse, name="locatii"),
]
