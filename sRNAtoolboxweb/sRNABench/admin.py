from django.contrib import admin

from .models import Species


class SpeciesAdmin(admin.ModelAdmin):
    pass

admin.site.register(Species, SpeciesAdmin)