from django.db import models
import uuid

# Create your models here.
class Locatie(models.Model):
    adresa = models.CharField(max_length=255)
    oras = models.CharField(max_length=100)
    judet = models.CharField(max_length=100)
    cod_postal = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.adresa}, {self.oras}"

class Masina(models.Model):
    id_masina = models.IntegerField()
    model = models.CharField(max_length=100)
    an_fabricatie = models.IntegerField()
    pret_masina = models.FloatField()
    in_stoc = models.BooleanField()
    id_marca = models.IntegerField()
    data_adaugarii = models.DateField()
    
class Marca(models.Model):
    id_marca = models.IntegerField()
    nume_marca = models.CharField(max_length=255)
    tara_origine = models.CharField(max_length=255)
    an_infiintare = models.IntegerField()

class Serviciu(models.Model):
    id_serviciu = models.IntegerField()
    nume_serviciu = models.CharField(max_length=255)
    pret_serviciu = models.FloatField()
    descriere_serviciu = models.TextField()

class CategorieMasina(models.Model):
    id_categorie = models.IntegerField()
    nume_categorie = models.CharField(max_length=255)
    descriere_categorie = models.TextField()
    tip_combustibil = models.CharField(max_length=255)

class Accesoriu(models.Model):
    id_accesoriu = models.IntegerField()
    nume_accesoriu = models.CharField(max_length=255)
    pret_accesoriu = models.FloatField()
    stoc_accesoriu = models.IntegerField()
