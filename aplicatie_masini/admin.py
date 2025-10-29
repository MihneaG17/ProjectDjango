from django.contrib import admin
from .models import Locatie, Masina, Marca, CategorieMasina, Serviciu, Accesoriu

admin.site.site_header = "Panou de Administrare Magazin de masini"
admin.site.site_title = "Admin Site Masini"
admin.site.index_title = "Bine ai venit în panoul de administrare"
# Register your models here.

#admin.site.register(Locatie)
admin.site.register(Marca)
admin.site.register(CategorieMasina)
admin.site.register(Serviciu)
admin.site.register(Accesoriu)
admin.site.register(Masina)

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


admin.site.register(Locatie, LocatieAdmin)