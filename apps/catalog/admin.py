from django.contrib import admin
from .models import Concours, Annee, Epreuve


@admin.register(Concours)
class ConcoursAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'description')
    search_fields = ('nom',)


@admin.register(Annee)
class AnneeAdmin(admin.ModelAdmin):
    list_display = ('id', 'valeur')
    ordering = ('-valeur',)


@admin.register(Epreuve)
class EpreuveAdmin(admin.ModelAdmin):
    list_display = ('id', 'titre', 'concours', 'annee')
    list_filter = ('concours', 'annee')
    search_fields = ('titre',)