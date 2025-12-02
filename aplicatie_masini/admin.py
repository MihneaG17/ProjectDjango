from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Locatie, Masina, Marca, CategorieMasina, Serviciu, Accesoriu, CustomUser

admin.site.site_header = "Panou de Administrare Magazin de masini"
admin.site.site_title = "Admin Site Masini"
admin.site.index_title = "Bine ai venit în panoul de administrare"

# Register your models here.

class LocatieAdmin(admin.ModelAdmin):
    list_display = ('oras', 'judet') #afiseaza campurile in lista de obiecte
    list_filter = ('oras', 'judet') #adauga filtre laterale
    search_fields = ('oras', ) #permite cautarea dupa anumite campuri
    fieldsets = (
        ('Date Generale', {
            'fields': ('oras', 'judet')
        }),
        ('Date Specifice', {
            'fields': ('adresa', 'cod_postal'),
            'classes': ('collapse',),  # secțiune pliabilă
        }),
    )

class MasinaAdmin(admin.ModelAdmin):
    ordering = ['pret_masina', '-kilometraj']
    search_fields=('model','an_fabricatie')
    list_display = ('model', 'marca', 'categorie')
    list_filter=['categorie', 'an_fabricatie', 'marca']
    list_per_page=5
    fieldsets= (
        ('Informatii Generale', {
            'fields': ('marca', 'categorie', 'model')
        }),
        ('Informatii Specifice', {
            'fields': ('kilometraj', 'tip_combustibil','pret_masina', 'an_fabricatie', 'in_stoc') 
        }),
        ('Suplimentare', {
            'fields': ('servicii', 'accesorii','imagine',),
            'classes': ('collapse',),
        }),
    )

class MarcaAdmin(admin.ModelAdmin):
    ordering = ['an_infiintare']
    search_fields=('nume_marca','tara_origine')
    list_filter=['tara_origine',]
    list_display = ('nume_marca', 'tara_origine')
    fields = ['an_infiintare', 'nume_marca', 'tara_origine']

class CategorieMasinaAdmin(admin.ModelAdmin):
    ordering = ['nume_categorie']
    search_fields=('nume_categorie', 'descriere')
    list_filter=['nume_categorie',]
    list_display = ('nume_categorie',)

class ServiciuAdmin(admin.ModelAdmin):
    ordering = ['-pret_serviciu']
    search_fields=('nume_serviciu', 'descriere_serviciu')
    list_display = ('nume_serviciu','pret_serviciu')

class AccesoriuAdmin(admin.ModelAdmin):
    ordering = ['-pret_accesoriu']
    search_fields=('nume_accesoriu', 'pret_accesoriu')
    list_display = ('nume_accesoriu','pret_accesoriu')

class CustomUserAdmin(admin.ModelAdmin):
    fieldsets= (
        ('Informatii Generale', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Informatii Specifice', {
            'fields': ('telefon', 'tara','judet', 'oras', 'strada', 'cod_postal', 'cod', 'email_confirmat') 
        }),
    )
admin.site.register(Locatie, LocatieAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Masina, MasinaAdmin)
admin.site.register(CategorieMasina, CategorieMasinaAdmin)
admin.site.register(Serviciu, ServiciuAdmin)
admin.site.register(Accesoriu, AccesoriuAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
