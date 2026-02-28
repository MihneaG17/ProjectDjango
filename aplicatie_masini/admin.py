from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Locatie, Masina, Marca, CategorieMasina, Serviciu, Accesoriu, CustomUser, IncercareLogare, Comanda, ItemComanda

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
            'fields': ('kilometraj', 'tip_combustibil','pret_masina', 'an_fabricatie', 'stoc') 
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

class CustomUserAdmin(UserAdmin):
    list_display=('username', 'email', 'first_name', 'last_name', 'is_staff', 'email_confirmat', 'blocat')
    fieldsets= (
        ('Cont', {
            'fields': ('username', 'password')
        }),
        ('Informatii personale', {
            'fields': ('first_name', 'last_name','email') 
        }),
        ('Informatii specifice', {
            'fields': ('telefon', 'oras', 'strada', 'cod_postal', 'cod', 'email_confirmat', 'blocat')
        }),
        ('Permisiuni', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    
    def get_readonly_fields(self, request, obj = None):
        readonly_fields=super().get_readonly_fields(request, obj)

        if request.user.is_superuser:
            return readonly_fields
        if request.user.has_perm('aplicatie_masini.blocheaza_utilizator'):
            return (
                'username', 
                'password',
                'is_superuser', 
                'is_staff', 
                'is_active',
                'groups', 
                'user_permissions',
                'last_login', 
                'date_joined',

                'telefon',
                'oras',
                'strada',
                'cod_postal',
                'cod',
                'email_confirmat', )
    
admin.site.register(Locatie, LocatieAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Masina, MasinaAdmin)
admin.site.register(CategorieMasina, CategorieMasinaAdmin)
admin.site.register(Serviciu, ServiciuAdmin)
admin.site.register(Accesoriu, AccesoriuAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(IncercareLogare)


class ItemComandaInline(admin.TabularInline):
    model = ItemComanda
    extra = 0
    fields = ['masina', 'cantitate', 'pret_unitar', 'subtotal']
    readonly_fields = ['subtotal']


class ComandaAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilizator', 'data_comanda', 'pret_total', 'numar_produse')
    list_filter = ['data_comanda', 'utilizator']
    search_fields = ['utilizator__username', 'utilizator__email']
    readonly_fields = ['data_comanda', 'pret_total']
    inlines = [ItemComandaInline]
    
    def numar_produse(self, obj):
        return obj.itemcomanda_set.count()
    numar_produse.short_description = 'Produse'
    
    fieldsets = (
        ('Informații Comandă', {
            'fields': ('utilizator', 'data_comanda', 'pret_total')
        }),
    )


admin.site.register(Comanda, ComandaAdmin)


"""
def get_readonly_fields(self, request, obj = None):
        readonly_fields=super().get_readonly_fields(request, obj)

        if request.user.is_superuser:
            return readonly_fields
        if request.user.has_perm('aplicatie_masini.blocheaza_utilizator'):
            campuri_permise=['first_name', 'last_name', 'email', 'blocat']
            toate_campurile_afisate=self.get_fields(request,obj)
            campuri_de_blocat=[]
            for nume in toate_campurile_afisate:
                if nume not in campuri_permise:
                    campuri_de_blocat.append(nume)
            return campuri_de_blocat
        return readonly_fields
"""