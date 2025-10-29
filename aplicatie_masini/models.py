from django.db import models
import uuid

# Create your models here.
class Locatie(models.Model):
    adresa = models.CharField(max_length=255)
    oras = models.CharField(max_length=100)
    judet = models.CharField(max_length=100)
    cod_postal = models.CharField(max_length=10)
    nr=models.IntegerField(default=0)

    def __str__(self):
        return f"{self.adresa}, {self.oras}"

class Marca(models.Model):
    #id_marca = models.IntegerField()
    nume_marca = models.CharField(max_length=255, unique=True)
    tara_origine = models.CharField(max_length=255)
    an_infiintare = models.IntegerField()
    
    def __str__(self):
        return self.nume_marca
    
class CategorieMasina(models.Model):
    #id_categorie = models.IntegerField()
    nume_categorie = models.CharField(max_length=255)
    descriere = models.TextField()
    
    def __str__(self):
        return self.nume_categorie
 
class Serviciu(models.Model):
    #id_serviciu = models.IntegerField()
    nume_serviciu = models.CharField(max_length=255)
    pret_serviciu = models.FloatField()
    descriere_serviciu = models.TextField(null=True)
    
    def __str__(self):
        return self.nume_serviciu

class Accesoriu(models.Model):
    #id_accesoriu = models.IntegerField()
    nume_accesoriu = models.CharField(max_length=255)
    pret_accesoriu = models.FloatField()
    stoc_accesoriu = models.IntegerField()
    
    def __str__(self):
        return self.nume_accesoriu
    
class Masina(models.Model):
    
    class TipCombustibil(models.TextChoices):
        BENZINA = 'BENZINA', 'Benzină'
        DIESEL = 'DIESEL', 'Diesel'
        ELECTRIC = 'ELECTRIC', 'Electric'
        HIBRID = 'HIBRID', 'Hibrid'
        GPL = 'GPL', 'GPL'
        ALTUL = 'ALTUL', 'Altul'
        
    #id_masina = models.IntegerField() - gestionat automat de django
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    categorie = models.ForeignKey(CategorieMasina, on_delete=models.CASCADE)
    pret_masina = models.FloatField()
    in_stoc = models.BooleanField(default = True)
    model = models.CharField(max_length=100)
    an_fabricatie = models.IntegerField()
    kilometraj = models.IntegerField(default = 0)
    tip_combustibil = models.CharField(
        max_length=100,
        choices = TipCombustibil.choices,
        default = TipCombustibil.BENZINA
        )
    data_adaugarii = models.DateField(auto_now_add=True)
    
    servicii = models.ManyToManyField(Serviciu, blank=True)
    accesorii = models.ManyToManyField(Accesoriu, blank=True)
    
    def __str__(self):
        return f"{self.marca.nume_marca} {self.model} ({self.an_fabricatie})"

